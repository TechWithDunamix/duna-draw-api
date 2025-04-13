from typing import List, Optional
from pydantic import BaseModel
from nexios import get_application
from nexios.exceptions import HTTPException
from nexios.http import Request, Response
from nexios.routing import Router
import pyfiglet
from pyfiglet import FigletFont

# Create the app
app = get_application()

# Pydantic Models
class FigletRequest(BaseModel):
    text: str
    font: str = "standard"
    width: Optional[int] = 80
    justify: Optional[str] = "center"  # left/center/right

class FigletResponse(BaseModel):
    ascii_art: str
    font_used: str
    metadata: dict

class FontListResponse(BaseModel):
    fonts: List[str]
    count: int

# Create router
figlet_router = Router(prefix="/figlet")

# Startup - Load available fonts
@app.on_startup
async def load_fonts():
    print("PyFiglet API ready with", len(FigletFont.getFonts()), "fonts!")

# Helper functions
def justify_text(text: str, width: int, alignment: str) -> str:
    lines = text.split('\n')
    justified = []
    for line in lines:
        if alignment == "center":
            justified.append(line.center(width))
        elif alignment == "right":
            justified.append(line.rjust(width))
        else:  # left
            justified.append(line.ljust(width))
    return '\n'.join(justified)

# Routes
@figlet_router.post("/generate", responses=FigletResponse, tags=["core"], request_model=FigletRequest,
                     summary="Generate custom ASCII art",
    description="""Convert text to ASCII art using various Figlet fonts.
    
**Features:**
- Choose from hundreds of fonts
- Control output width
- Justify text (left, center, right)
    
**Example:**
```json
{
    "text": "Hello World",
    "font": "banner",
    "width": 100,
    "justify": "center"
}
```""")
async def generate_ascii(request: Request, response: Response):
    """Generate ASCII art from text"""
    try:
        body = await request.json
        req = FigletRequest(**body)
        
        # Validate font exists
        available_fonts = FigletFont.getFonts()
        if req.font not in available_fonts:
            raise HTTPException(
                status_code=400,
                detail=f"Font not found. Available fonts: {available_fonts[:5]}... ({len(available_fonts)} total)"
            )
        
        # Generate ASCII art
        ascii_art = pyfiglet.figlet_format(
            req.text,
            font=req.font,
            width=req.width
        )
        
        # Apply justification
        ascii_art = justify_text(ascii_art, req.width, req.justify)
        
        return response.json({
            "ascii_art": ascii_art,
            "font_used": req.font,
            "metadata": {
                "original_text": req.text,
                "width": req.width,
                "alignment": req.justify,
                "line_count": len(ascii_art.split('\n'))
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@figlet_router.get("/fonts", responses=FontListResponse, tags=["discovery"], 
                   summary="List all available fonts",
    description="""Returns a comprehensive list of all Figlet fonts available in the system.
    
**Response includes:**
- List of font names
- Total count of available fonts
    
**Note:** Fonts can be used with the `/generate` endpoint.""")
async def list_fonts(request: Request, response: Response):
    """List all available fonts"""
    fonts = FigletFont.getFonts()
    return response.json({
        "fonts": fonts,
        "count": len(fonts)
    })

@figlet_router.get("/random", responses=FigletResponse, tags=["fun"])
async def random_art(request: Request, response: Response):
    """Generate random ASCII art"""
    from random import choice
    fonts = FigletFont.getFonts()
    sample_texts = [
        "Hello World",
        "ASCII Rocks",
        "PyFiglet",
        "Nexios",
        "Make Art"
    ]
    
    return response.json({
        "ascii_art": pyfiglet.figlet_format(
            choice(sample_texts),
            font=choice(fonts)
        ),
        "font_used": choice(fonts),
        "metadata": {
            "note": "Randomly generated"
        }
    })

# Mount router
app.mount_router(figlet_router)

# Root endpoint
@app.get("/")
async def root(request: Request, response: Response):
    return response.json({
        "message": "PyFiglet API",
        "endpoints": {
            "/figlet/generate": "POST - Create custom ASCII art",
            "/figlet/fonts": "GET - List all fonts",
            "/figlet/random": "GET - Random ASCII art"
        },
        "example_request": {
            "method": "POST",
            "url": "/figlet/generate",
            "body": {
                "text": "Hello",
                "font": "banner",
                "width": 100,
                "justify": "center"
            }
        }
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)