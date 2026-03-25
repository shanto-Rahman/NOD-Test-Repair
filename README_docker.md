unzip hbase.zip
docker load -i hbase.tar
docker run -it --name hbase_test --memory="16g" --cpus="4" hbase:latest /bin/bash
. $HOME/.profile
cd /projects/hbase
