from pydantic import BaseModel
from datetime import datetime, time, date
import uuid
from typing import List


curdate = datetime.now().date()
print(type(curdate))
isodate = curdate.isoformat()
print(type(isodate))
print(type(date.fromisoformat(isodate)))
