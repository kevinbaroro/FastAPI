
from fastapi import FastAPI, UploadFile, File,HTTPException
from pydantic import BaseModel
import pdfquery
import fitz
import tempfile
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from io import BytesIO


app = FastAPI()

class OCRResult(BaseModel):
    po_number: str
    po_date: str
    vendor_code: str


# Define a route to add an image to a PDF
@app.post('/addimage')
async def add_image_to_pdf(pdf_file: UploadFile, image_file: UploadFile):
    try:
        if not pdf_file:
            raise HTTPException(status_code=400, detail='No PDF file provided')

        if not image_file:
            raise HTTPException(status_code=400, detail='No image file provided')

        # Open the PDF file and create a PyMuPDF Document object
        pdf_data = await pdf_file.read()
        pdf_document = fitz.open(stream=pdf_data, filetype="pdf")

        # Open the image file
        image_data = await image_file.read()

        # Get the first page of the PDF (change the page number if needed)
        page = pdf_document[0]

        # Get the page's media box coordinates
        page_rect = page.rect

        # Calculate the width and height of the page
        page_width = page_rect[2]
        page_height = page_rect[3]

        # Define the image dimensions
        image_width = 150  # Adjust this to the width of your image
        image_height = 180  # Adjust this to the height of your image

        # Calculate the coordinates to place the image at the bottom right
        x = page_width - image_width
        y = page_height - image_height  # Set to the difference to align with the bottom

        # Add the image to the page
        page.insert_image((x, y, x + 110, y + 190), stream=BytesIO(image_data))



        # Save the modified PDF
        output_pdf = BytesIO()
        pdf_document.save(output_pdf,deflate=True)
        pdf_document.close()

        # Return the modified PDF as a streaming response
        return StreamingResponse(BytesIO(output_pdf.getvalue()), media_type='application/pdf')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@app.post("/find_word", response_model=OCRResult)
async def find_word(pdf_file: UploadFile):
   
        try:
            if not pdf_file:
                raise HTTPException(status_code=400, detail='No PDF file provided')

            # Open the PDF file and create a PyMuPDF Document object
            pdf_data = await pdf_file.read()
            pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
   
            # Get the first page of the PDF
            page = pdf_document[0]

            # Extract sorted words from the first page
            words = page.get_text("words", sort=True)

            for i, word in enumerate(words):
                # Check for specific keywords in the text and extract corresponding values
                if word[4] == "VENDOR":
                    vendor_code = words[i + 5][4]
                elif word[4] == "DATE":
                    po_date = words[i + 2][4]
                elif word[4] == "P.O.":
                    po_number = words[i + 3][4]


            result = OCRResult(po_number=po_number,po_date=po_date, vendor_code=vendor_code)
            # Return the OCR result as JSON
            return result
        
        except Exception as e:
                return JSONResponse(content={"error": str(e)}, status_code=500)