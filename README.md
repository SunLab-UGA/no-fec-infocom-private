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
