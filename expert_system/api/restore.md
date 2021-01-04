# Register

Resgister a new virtual fireman to the expert system

**URL** : `register`

**Method** : `POST`

**Auth required** : NO

**Data constraints** :

```json
{
    "id" : "[int]",
    "url": "[sensor url]"
}
```

**Data example** :

```json
{
    "id" : 1,
    "url": "http://localhost:7654/"
}
```

## Success Response

**Code** : `204 OK`
