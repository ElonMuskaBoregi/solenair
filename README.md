# solenair
An air quality monitoring panel for a particule concentration reduction project. Using streamlit and CSS for the base, this app imports the data from the device, uploads it by the consent of the admin via the admin panel, creates graphics for desired time periods, with an integrated Ollama gemma3:4b AI model interpretating the data. 

In order to start the program, change the directory over the one that the file is saved. Then, download the required libraries, mentioned in the first lines of the code. Afterwards, create a virtual environment within the directory in Python for optimisation. Then, check if the Plotly version is up-to-date. Then, create a folder in the directory, locate the config file within the folder, and type the following code in the Terminal: 
cd ~/yourdirectory
mkdir -p .foldername && mv config.toml .foldername/
Finally, type streamlit run solenair.py and you are good to go. 
