# xlorm

Python library ORM over Excel files for reading data (and writing with future developments) using a dead simple API.


## Usage

```python
from xlorm import BooleanColumn, DateColumn, NumberColumn, TextColumn, XLSSheetModel


class Car(XLSSheetModel):
    brand = TextColumn(column_index=0)
    model = TextColumn(column_index=1)
    year = DateColumn(column_index=2)
    units = NumberColumn(column_index=3)
    in_production = BooleanColumn(column_index=4)


for car in Car.all(filename='cars.xlsx'):
    print(car.brand)
    # do a lot more!
```


## Development

```bash
python3 -m venv venv  # `pip install virtualenv` for Python 2
virtualenv venv
source venv/bin/activate
pip install -r dev-requirements.txt
tox  # add `-p auto` to run in parallel
```
