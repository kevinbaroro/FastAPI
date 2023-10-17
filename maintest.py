from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
import tempfile
import pdfquery
from lxml import etree
from pydantic import BaseModel

app = FastAPI()

class OCRResult(BaseModel):
    po_number: str
    vendor_code: str

@app.post("/find_word", response_model=OCRResult)
async def find_word(pdf_file: UploadFile):
    try:
        if pdf_file:
            # Create a temporary file to save the uploaded PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_temp_file:
                pdf_temp_file.write(pdf_file.file.read())
                pdf_temp_file_path = pdf_temp_file.name

            pdf = pdfquery.PDFQuery(pdf_temp_file_path)
            pdf.load()

            # Create a temporary file for the XML data
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as xml_temp_file:
                xml_temp_file_path = xml_temp_file.name
                pdf.tree.write(xml_temp_file_path, pretty_print=True)

            # Find fields
            po_number = pdf.pq('LTTextBoxHorizontal:in_bbox("397.944, 527.256, 455.752, 535.256")').text()
            vendor_code = pdf.pq('LTTextBoxHorizontal:in_bbox("162.72, 514.152, 199.192, 522.152")').text()

            result = OCRResult(po_number=po_number, vendor_code=vendor_code)

            # Return the OCR result as JSON

            return result

        return JSONResponse(content={"error": "No PDF file content provided"}, status_code=400)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)