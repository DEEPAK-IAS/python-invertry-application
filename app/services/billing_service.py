from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.sale import Sale, SaleItem, Payment
from app.models.product import Product
from app.utils.pdf_generator import generate_invoice_pdf
from loguru import logger
from app.models.customer import Customer
import os


def _print_pdf_native(pdf_path: str, printer_name: str) -> bool:
    """Renders each PDF page as an image and sends it directly to the
    printer using Windows GDI — no external PDF viewer needed."""
    import fitz  # PyMuPDF
    import win32print
    import win32ui
    from PIL import Image, ImageWin

    pdf = fitz.open(pdf_path)
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)
    hDC.StartDoc(os.path.basename(pdf_path))

    HORZRES, VERTRES = 8, 10
    printable_w = hDC.GetDeviceCaps(HORZRES)
    printable_h = hDC.GetDeviceCaps(VERTRES)

    try:
        for page_index in range(len(pdf)):
            page = pdf[page_index]
            zoom = 3  # ~216 DPI render — sharp enough for text/tables
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Scale to fit the printable area while keeping aspect ratio
            img_ratio = pix.width / pix.height
            page_ratio = printable_w / printable_h
            if img_ratio > page_ratio:
                new_w = printable_w
                new_h = int(printable_w / img_ratio)
            else:
                new_h = printable_h
                new_w = int(printable_h * img_ratio)

            x = (printable_w - new_w) // 2
            y = (printable_h - new_h) // 2

            hDC.StartPage()
            dib = ImageWin.Dib(img)
            dib.draw(hDC.GetHandleOutput(), (x, y, x + new_w, y + new_h))
            hDC.EndPage()
    finally:
        hDC.EndDoc()
        pdf.close()

    return True

def _try_print(pdf_path: str, preferred_printer: str = "") -> bool:
    """
    Try to print the PDF if a printer is available.
    Returns True if printed, False if no printer found.
    """
    try:
        import win32print

        printers = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        if not printers:
            logger.info("No printer found — PDF saved only.")
            return False

        default_printer = preferred_printer or win32print.GetDefaultPrinter()
        logger.info(f"Printing to: {default_printer}")

        try:
            _print_pdf_native(pdf_path, default_printer)
            logger.info(f"Invoice printed natively: {pdf_path}")
            return True
        except Exception as native_err:
            logger.warning(
                f"Native printing failed ({native_err}) — "
                f"falling back to Windows default print handler."
            )
            os.startfile(pdf_path, "print")
            logger.info(f"Invoice sent via Windows default print handler: {pdf_path}")
            return True

    except ImportError as e:
        logger.warning(f"Printing module not available — PDF saved only. ({e})")
        return False
    except Exception as e:
        logger.warning(f"Printing failed — PDF saved only. Reason: {e}")
        return False

class BillingService:
    @staticmethod
    def process_checkout(
        db: Session,
        customer_data: dict,
        cart_items: list,
        is_gst: bool,
        company_name: str,
        company_address: str,
        company_gst: str = "",
        company_phone: str = "",
        company_email: str = "",
        company_logo_path: str = "",
        preferred_printer: str = "",
        amount_paid: float = None,
    ) -> Sale:
        """
        amount_paid: how much the customer is paying right now.
            - None (default)        -> treated as full payment (backwards compatible)
            - < grand total         -> the difference becomes a "pending bill" (due_amount)
            - 0                     -> fully unpaid / on credit
        """
        try:
            subtotal  = 0.0
            total_gst = 0.0

            # --- Customer Persistence ---
            name  = customer_data.get("name", "").strip()
            phone = customer_data.get("phone", "").strip()

            if phone and name and name != "Walk-in":
                address = customer_data.get("address", "").strip()
                customer = db.query(Customer).filter(Customer.phone == phone).first()
                if not customer:
                    new_customer = Customer(name=name, phone=phone, address=address or None)
                    db.add(new_customer)
                    db.commit()
                    db.refresh(new_customer)
                elif address and not customer.address:
                    customer.address = address
                    db.commit()

            # Extract discount values passed from SalesWindow
            discount_pct = customer_data.get("discount_percentage", 0.0)
            discount_amt = customer_data.get("discount_amount", 0.0)

            # 1. Initialize Sale Record
            sale = Sale(
                customer_name=customer_data.get("name", "Walk-in Customer"),
                customer_phone=customer_data.get("phone", ""),
                customer_gstin=customer_data.get("gstin", ""),
                customer_address=customer_data.get("address", ""),
                is_gst_bill=is_gst,
                gst_rate=0.0,
                discount_percentage=discount_pct,
                discount_amount=discount_amt,
            )
            db.add(sale)
            db.flush()

            # 2. Process Items
            for item in cart_items:
                product = db.query(Product).filter(Product.id == item["product_id"]).first()
                if not product or product.stock_qty < item["quantity"]:
                    raise ValueError(f"Insufficient stock for {item['name']}")

                product.stock_qty -= item["quantity"]

                item_total    = item["quantity"] * item["price"]
                item_gst_rate = item.get("gst_rate") or getattr(product, "gst_rate", 0.0) or 0.0
                subtotal     += item_total

                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    product_name=item["name"],
                    size=getattr(product, "size", "") or "",
                    quantity=item["quantity"],
                    unit_price=item["price"],
                    total_price=item_total,
                    gst_rate=item_gst_rate,
                )
                db.add(sale_item)

            # Apply proportional adjustment or direct subtraction for tax calculation based on discount
            taxable_subtotal = max(0.0, subtotal - discount_amt)
            ratio = taxable_subtotal / subtotal if subtotal > 0 else 1.0

            if is_gst:
                for item in cart_items:
                    item_total = item["quantity"] * item["price"]
                    item_gst_rate = item.get("gst_rate") or 0.0
                    total_gst += (item_total * ratio) * (item_gst_rate / 100)

            # 3. Finalize Totals
            sale.subtotal     = subtotal
            sale.gst_amount   = total_gst
            sale.total_amount = taxable_subtotal + total_gst

            # 3b. Pending Bill / Partial Payment handling
            grand_total = sale.total_amount
            paid = grand_total if amount_paid is None else max(0.0, min(amount_paid, grand_total))
            due  = round(grand_total - paid, 2)

            sale.paid_amount = round(paid, 2)
            sale.due_amount  = due
            if due <= 0.001:
                sale.payment_status = "PAID"
            elif paid <= 0.001:
                sale.payment_status = "UNPAID"
            else:
                sale.payment_status = "PARTIAL"

            if paid > 0:
                db.add(Payment(sale_id=sale.id, amount=paid, note="Initial payment at checkout"))

            # 4. Commit
            db.commit()
            logger.info(
                f"Sale #{sale.id} processed. Total: {grand_total:.2f}, "
                f"Paid: {sale.paid_amount:.2f}, Due: {sale.due_amount:.2f}"
            )

            # 5. Generate PDF
            pdf_path = generate_invoice_pdf(
                sale,
                company_name=company_name,
                company_address=company_address,
                company_gst=company_gst,
                company_phone=company_phone,
                company_email=company_email,
                company_logo_path=company_logo_path,
            )
            logger.info(f"Invoice PDF saved: {pdf_path}")

            # 6. Auto-print if printer available, else PDF only
            printed = _try_print(pdf_path, preferred_printer=preferred_printer)
            if printed:
                logger.info(f"Invoice #{sale.id} sent to printer.")
            else:
                logger.info(f"Invoice #{sale.id} saved as PDF only: {pdf_path}")

            return sale

        except Exception as e:
            db.rollback()
            logger.error(f"Checkout failed: {e}")
            raise e

    @staticmethod
    def record_payment(db: Session, sale_id: int, amount: float, note: str = "") -> Sale:
        """
        Records a new payment against an existing (pending) bill and updates
        the sale's paid_amount / due_amount / payment_status accordingly.
        """
        try:
            sale = db.query(Sale).filter(Sale.id == sale_id).first()
            if not sale:
                raise ValueError(f"Invoice #{sale_id} not found.")

            if amount is None or amount <= 0:
                raise ValueError("Payment amount must be greater than zero.")

            if amount > sale.due_amount + 0.01:
                raise ValueError(
                    f"Payment (₹{amount:.2f}) exceeds the pending due (₹{sale.due_amount:.2f})."
                )

            db.add(Payment(sale_id=sale.id, amount=amount, note=note or ""))

            sale.paid_amount = round((sale.paid_amount or 0.0) + amount, 2)
            sale.due_amount  = round(sale.total_amount - sale.paid_amount, 2)
            sale.payment_status = "PAID" if sale.due_amount <= 0.001 else "PARTIAL"

            db.commit()
            db.refresh(sale)
            logger.info(f"Payment of ₹{amount:.2f} recorded for Sale #{sale.id}. Due now ₹{sale.due_amount:.2f}")
            return sale
        except Exception as e:
            db.rollback()
            logger.error(f"Recording payment failed: {e}")
            raise e

    @staticmethod
    def cancel_invoice(db, sale_id: int):
        """Cancels an invoice and restores stock."""
        from app.models.sale import Sale

        try:
            sale = db.query(Sale).filter(Sale.id == sale_id).first()
            if not sale:
                raise ValueError(f"Invoice #{sale_id} not found.")

            for item in getattr(sale, "items", []):
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product.stock_qty += item.quantity

            db.delete(sale)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def print_pdf(pdf_path: str, preferred_printer: str = "") -> bool:
        return _try_print(pdf_path, preferred_printer=preferred_printer)