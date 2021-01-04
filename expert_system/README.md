# Expert System

The code present here implements a simple expert system based on a state machine.

## Prerequisites

Create a virtual environment, activate it and install the requirements:

```console
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## REST API

* [Register](api/register.md) : `POST /register`
* [Save](api/save.md)         : `GET /save/:ids`
* [Restore](api/restore.md)   : `POST /restore`
* [Rank](api/rank.md)         : `GET /rank/:n`
* [Sensor](api/sensor.md)     : `PUT /sensor/:id`
* [Deploy](api/deploy.md)     : `PUT /deploy/:ids`

## Authors

* **Mário Antunes** - [mariolpantunes](https://github.com/mariolpantunes)
