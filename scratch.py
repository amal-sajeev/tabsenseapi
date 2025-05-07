from pydantic import BaseModel
from datetime import datetime, time
import uuid
from typing import List

#HOLIDAYS CRUD
class Holiday(BaseModel):
    id: str= str(uuid.uuid4())
    label: str
    start:str
    end:str
    rooms:List[str]

hola = Holiday(label= "Christmas", start = datetime.now().date().isoformat(), end  = datetime.now().date().isoformat(), rooms = ["lobby","hall"] )

print(hola)
print(hola.dict)