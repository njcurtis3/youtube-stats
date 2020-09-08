# Articles of Unity Campfire Data Collection

Fetch the dependencies:
```bash
$ pip install -r requirements.txt
```

**THE FOLLOWING INSTRUCTIONS WILL AFFECT PRODUCTION DATA IF THE TABLE_ID HAS NOT BEEN CHANGED**

**If any changes need to be made to the shape of the data, copy the dataset in BigQuery and test your changes against the duplicate**

To run the portion of the function doing the work, you will need to invoke it from the python repl.
```bash
$ GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json" python
Python 3.8.5 (default, Aug  5 2020, 08:22:02) 
[GCC 8.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import main
>>> from datetime import datetime
>>> current_time = datetime.utcnow().isoformat(timespec="seconds") + "Z"
>>> main.run(current_time)
```

## Setting up the development container
**This is only neccessary if you prefer not to set up a local python toolchain**

Follow these steps to open the repo in the development container:

1. If this is your first time using a development container, please follow the [getting started steps](https://aka.ms/vscode-remote/containers/getting-started).

2. To use this repository, open a locally cloned copy of the code:

   - Clone this repository to your local filesystem.
   - Press <kbd>F1</kbd> and select the **Remote-Containers: Open Folder in Container...** command.
   - Select the cloned copy of this folder, wait for the container to start, and try things out!

