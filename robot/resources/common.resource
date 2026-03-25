*** Settings ***
Library    RequestsLibrary

*** Variables ***
${BASE_URL}    http://127.0.0.1:8010
&{VALID_HEADERS}    X-API-Key=demo-key
&{INVALID_HEADERS}    X-API-Key=invalid-key