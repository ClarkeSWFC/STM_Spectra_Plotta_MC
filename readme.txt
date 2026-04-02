 __  __  ____  _  _  ____/ ___      __    ____  ___  _____  __    __  __  ____  ____  __   _  _ 
(  \/  )(_  _)( )/ )( ___)/ __)    /__\  (  _ \/ __)(  _  )(  )  (  )(  )(_  _)( ___)(  ) ( \/ )
 )    (  _)(_  )  (  )__) \__ \   /(__)\  ) _ <\__ \ )(_)(  )(__  )(__)(   )(   )__)  )(__ \  / 
(_/\/\_)(____)(_)\_)(____)(___/  (__)(__)(____/(___/(_____)(____)(______) (__) (____)(____)(__) 
               ____  _  _  ___    __    _  _  ____    ___  ____  __  __                         
              (_  _)( \( )/ __)  /__\  ( \( )( ___)  / __)(_  _)(  \/  )                        
               _)(_  )  ( \__ \ /(__)\  )  (  )__)   \__ \  )(   )    (                         
              (____)(_)\_)(___/(__)(__)(_)\_)(____)  (___/ (__) (_/\/\_)                        
 ___  ____  ____  ___  ____  ____    __      _  _  ____  ____  _    _  ____  ____               
/ __)(  _ \( ___)/ __)(_  _)(  _ \  /__\    ( \/ )(_  _)( ___)( \/\/ )( ___)(  _ \              
\__ \ )___/ )__)( (__   )(   )   / /(__)\    \  /  _)(_  )__)  )    (  )__)  )   /              
(___/(__)  (____)\___) (__) (_)\_)(__)(__)    \/  (____)(____)(__/\__)(____)(_)\_)   
---Installation---

1.extract zip/download all from github into wherever
2.ensure your python has all modules installed (they are listed at the top of the various python files)
3.run main.py
4.PROFIT

---tl;dr---
This program plots the positions at which spectra have been taken, onto the most recently taken STM image. It also allows the plotting of the associated spectra alongside the STM image. This program is only compatible with nanonis produced STM images and spectra.

~~~~~What do the buttons do?~~~~~
LEFT
---Select Data Folder---
This folder should contain both the relevant STM images and spectra. I believe nanonis puts them in the same place by default. If you have selected an appropriate folder, the scans in the folder should appear in the list below. You can select an STM image by clicking it in the list, and any associated spectra should appear in the list on the right hand side.

UNDER STM Plot
---Label Every N Spectra---
Can change how many spectra get a numerical label. Helpful to select bigger numbers when you have a lot of closely spaced spectra positions.

---Label offset---
Adds transparency and offsets the labels for the spots so that the spot locations can be seen with greater ease.

---Show spectra positions---
The positions of spectra shown on the STM plot can be toggled on and off.

---Subtract mean plane--- 
Crude mean plane subtraction to improve quality of STM image if slanted.

UNDER SPECTRA PLOT
---X axis and Y axis---
Choose which channels to use as X and Y axis for spectra plot

---Both Dirs---
Plots both forwards and backwards spectra (if available). If this box is unchecked, it just shows forwards.

---Sum Dirs---
Sums the forwards and backwards spectra (if available).

---KPFM Fit---
Performs a KPFM fit onto a frequency shift curve, producing a value for the contact potential. Ask Sofia about this, I just plugged it in.

---Invert Y---
Inverts the Y axis.


Scroll down for Gollum
           ___
         .';:;'.
        /_' _' /\   __
        ;a/ e= J/-'"  '.
        \ ~_   (  -'  ( ;_ ,.
         L~"'_.    -.  \ ./  )
         ,'-' '-._  _;  )'   (
       .' .'   _.'")  \  \(  |
      /  (  .-'   __\{`', \  |
     / .'  /  _.-'   "  ; /  |
    / /    '-._'-,     / / \ (
 __/ (_    ,;' .-'    / /  /_'-._
`"-'` ~`  ccc.'   __.','     \j\L\
                 .='/|\7      
     snd           ' `

