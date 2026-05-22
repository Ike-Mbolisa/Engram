# Gauss - Data logger with Python and C

Overview
------------------------------------------------------------------------------
Gauss is a data logging program for cars. 
It connects to an OBDII Adapter connected to a car, and while the ignition is on, it will log RPM and Velocity of the car. 
Currently only compatible with a 2021 Qashqai

Gauss has the following features:
 - Can export CSV Filer
 - Can export Metric
 - Can connect to an OBDII Adapter and receive data

Usage
------------------------------------------------------------------------------
Gauss is launched directly from the code editor. 
It requires bluetooth connection to receive data from the car 
Although by launching from the code editor, you will need to download the packages used in the program

Work in progress / Acknowledgements
------------------------------------------------------------------------------
As of Version 0.8, the program is still missing many things from the final vision. 

This includes: 
 - ~~Compatibility with other cars~~ 
 - ~~Proper data logging~~ 
 - ~~Ui~~
 - Portability
 - Launching outside of Visual Studio Code, or any code editor

At the moment the program is only able to receive data from a 2021 Qashqai. This will be addressed in later versions, alongside other limitations 


////


# Gauss - Dataregistrering med Python og C

Overblik
------------------------------------------------------------------------------
Gauss er et dataregistrerings program til biler. 
Programmet forbinder sig med en OBDII Adapter som er tilsluttet til en bil. Mens det er at motoren er tændt, registrere den omdrejninger og hastigheden i bilen. 
I øjeblikket kan programmet bruges i en 2021 Qashqai.

Gauss kan følgende: 

- Exportere til CSV Filer
- Exportere i metriske enheder
- Danne forbindelse med en OBDII Adapter og modtag data

Anvendelse
------------------------------------------------------------------------------
Gauss skal startes fra en kodeeditor som Visual Studio eller VS Code
Det kræver Bluetooth forbindelse for at modtage data fra bilen
Dog hvis man starter det fra Visual Studio eller VS Code, kræver det at man har installeret Python pakkerne der bliver brugt


Under vejs / Anerkendelser
------------------------------------------------------------------------------
Lige nu i version 0.8, mangler programmet stadig en del. 
Det inkludere:

- ~~Kompatibilitet med andre biler~~
- ~~Bedre dataregristrering~~
- ~~Ui~~
- bærbarhed
- Opstart udenfor Visual Studio og VS Code
