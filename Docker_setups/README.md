Create the docker image using the following command in the terminal:

```bash
docker build -t nod-repair-env .
```

Then run the docker container in the interactive mode using the following command:

```bash
docker run -it --rm -v "$(pwd)/../NOD-Test-Repair:/NOD-Test-Repair" nod-repair-env /bin/bash
```
Assumption: You have cloned the `NOD-Test-Repair` repository and are running the above command from the `Docker_setups` directory.
This will mount the `NOD-Test-Repair` directory from your local machine to the `/NOD-Test-Repair` directory in the docker container, allowing you to access and work with the files inside the container.