
# Odyssean Travel Planner

Simple web app for easier trip planning and comparison. I created it for personal use, to be able to visualize my budget better.


## Features

- Create multiple trips with separate components.
- Activate/deactivate components without the need to delete.
- Get currency exchange rates once every 24 hours.
- Dynamic accurate exchange rates calculation.
- Dynamic graph updates.
- Ability to choose a preferred currency.


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`SECRET_KEY`
`DATABASE_URL`
`DATABASE_PASSWORD`

Structured as such (input your data in <> brackets)
![image](https://github.com/user-attachments/assets/a22564cb-be69-4cba-b02e-c418e21b615e)
## Deployment

You need to have an installation of Docker Desktop running to launch the web app.
To deploy this project run

```bash
docker compose up --build
```

## Tech Stack

**Client:** HTML, Jinja2, CSS, JS, Plotly Express

**Server:** Flask, Docker compose, Gunicorn, Dash

## Color Reference
In the project I use a color scheme for the component categories, here it is to make reading the app easier:

| Color             | Hex                                                                |
| ----------------- | ------------------------------------------------------------------ |
| Accommodation | ![#EA4848](https://placehold.co/15x15/EA4848/EA4848.png) #EA4848
| Food | ![#4FB477](https://placehold.co/15x15/4FB477/4FB477.png) #4FB477
| Transport | ![#85CCFF](https://placehold.co/15x15/85CCFF/85CCFF.png) #85CCFF
| Entertainment | ![#A975A4](https://placehold.co/15x15/A975A4/A975A4.png) #A975A4
| Shopping | ![#FF9B42](https://placehold.co/15x15/FF9B42/FF9B42.png) #FF9B42
| Other | ![#B8B8B8](https://placehold.co/15x15/B8B8B8/B8B8B8.png) #B8B8B8


## Screenshots
User view
![image](https://github.com/user-attachments/assets/112d6862-589c-405c-bf4f-6db6870db7fd)
Ability to change user info
![image](https://github.com/user-attachments/assets/fb9086af-75ce-41b0-928f-a6f89261d557)
Main trip view
![image](https://github.com/user-attachments/assets/1d4a7665-0902-40a1-9957-d0958e7c0975)


## Running Tests

To run tests, run the following command in the travel-planner directory

```bash
  python tests.py
```


## Acknowledgements

 - [wait-for-it.sh script by vishnubob](https://github.com/vishnubob/wait-for-it) *used during the development*
 - [fxratesapi for currency exchange rate updates](https://fxratesapi.com) *used once very 24 hours for fetching rates*

