# redfish_advantech

## Build package
- cd to the directory of setup.py
- Confirm the version number in setup.py and src/redfish_advantech/__init__.py

python setup.py sdist build
twine upload dist/*

## Uninstall the redfish_advantech
pip uninstall redfish_advantech -y

## Install the redfish_advantech
pip install redfish_advantech

or

pip install redfish_advantech==x.y.z
- where the x.y.z is the version number

## Test (Change to the directory which has logging.conf)
- Make sure the python is version 3.x
- Make sure the logging.conf is exist in the same directory as test sample code
- Add "-v", "-vv" or "-vvv" for more log

cd examples
<br/>python advantech.py
<br/>python acl_bmc.py
<br/>python acl_bmc_cm.py

＃Appendix:
<br/>❯ pip3
<br/>Traceback (most recent call last):
<br/>  File "/Users/ch.huang789/redfish_advantech_library/redfish/bin/pip3", line 5, in <module>
<br/>    from pip._internal.cli.main import main
<br/>ModuleNotFoundError: No module named 'pip'

Solution for macos:
<br/>❯ python3 -m ensurepip

