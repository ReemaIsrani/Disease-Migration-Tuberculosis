import requests
import pandas as pd
import base64
import pickle
import hug
import json
loc='MAHARASHTRA_SOLAPUR'
rspm=1
no2=2
so2=3
rainfall=0
humidity=0
temperature=-1
data={'loc':loc,'rspm':rspm,'no2':no2,'so2':so2,'rainfall':rainfall,'humidity':humidity, 'temperature':temperature}
response = requests.post('https://beprojectdm.pythonanywhere.com/dm',data=json.dumps(data)).json()
df=pickle.loads(base64.b64decode(response['prediction'].encode()))
print(df)
