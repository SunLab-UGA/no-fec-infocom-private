# NO_FEC
This is an exploration of a GNU_Radio 802.11 without Forward Error Correction
The radioconda env is to keep keep the ieee802_11 packages seperated

## install instructions
* install radioconda and mamba
    * https://github.com/ryanvolz/radioconda
* create a new env (no_fec)
```
conda create -n no_fec 
conda activate no_fec
```
* install gnuradio and dependencies
```
mamba install gnuradio gnuradio-build-deps boost
```
* reopen env
```
conda deactivate
conda activate no_fec
```
* build/install gr-foo (gr-foo-maint-3.10)
### build/install commands
```
mkdir build
cd build
cmake -G Ninja -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DLIB_SUFFIX="" ..
cmake --build .
cmake --build . --target install
```
* build/install NO-FEC (gr-ieee802-11-maint-3.10_NO-FEC)
    *same build/install steps as above
    
* create a new env (fec)
* activate and install gnuradio and dependencies as above
* move or remove the build folder!
* build/install 
    * foo (gr-foo-maint-3.10)
    * symbol-mod (gr-ieee802-11-maint-3.10-_Symbol_MOD)


---

With everything installed we can now run the top level apps or a full federated training
* app_train, trains both clients on a subset of data and saves them as "client0" or "client1" model on that computer (the first run has no "server" model, so random weights are loaded)
* app_client0_to_server and app_client1_to_server send the weights and save them on the server
* app_server_federate does the federation of the weights (fed_avg)
* app_server_to_clients broadcast the new weights to the clients, both save the weights as a "server" model

* federate.py automatically runs the five scripts in a loop
* federate_with_checks automatically runs with error checking and accuracy checking


TODO:
fill out more instructions on the python control and analysis

Adjust Maximum Shared Memory (not persistent)
```
sudo sysctl -w kernel.shmmax=2147483648
```
Persistent
```
echo 'kernel.shmmax=2147483648' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```
