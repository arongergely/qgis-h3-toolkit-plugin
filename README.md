# H3 Toolkit Plugin for QGIS
H3 tools for to QGIS, powered by the open source [H3 library](https://h3geo.org/">https://h3geo.org/)

## How to Install
Plugin is not available in the official QGIS plugin repository (yet! I am working on it) 
Until that happens you can download a zipped release from here and [install from ZIP](https://docs.qgis.org/3.22/en/docs/user_manual/plugins/plugins.html#the-install-from-zip-tab)

### Installing the `h3` dependency
***TL;DR If you are familiar with Python, this is straighforward via `pip` or `conda`. I am working to improve the install experience, but for now this is the way to go.*** 


The plugin depends on the `h3` python package, which you would have to install yourself into the Python environment of QGIS.
At startup the plugin detects if `h3` is missing from the python environment and offers basic guidance on how to install.

*NOTE: The plugin is tested with `h3` version `3.7.x` but in principle should work with other `3.x` versions.*

Please see [H3 Installation](https://h3geo.org/docs/installation) on how to install.

## How to use
A plugin registers an `H3` processing provider, the tools are available there.
Please have a look at the tool's help texts regarding specifics.

### Suggesting improvements / reporting issues
You are most welcome to post suggestions/issues on the [Issues page](https://github.com/arongergely/qgis-h3-toolkit-plugin/issues).

## Developer setup
Assuming a Linux developer environment:
1. clone this repository
2. Create a symbolic link in the plugin folder within your QGIS profile directory:
   
   To find your profile folder, open QGIS and navigate to *Settings -> User Profiles* and click on *Open Active Profile Folder*. 
   Then the plugin folder should be `<YOUR PROFILE FOLDER>/python/plugins/`

   `cd` into the plugin folder and create a symbolic link to the `h3_toolkit` folder of this repo. 
   ```shell
   ln -s /your/path/to/qgis-h3-toolkit-plugin/h3_toolkit h3_toolkit
   ```

### How to make a release
Simply zip up the `h3_toolkit` directory. The .zip file is then ready for [install from ZIP](https://docs.qgis.org/3.22/en/docs/user_manual/plugins/plugins.html#the-install-from-zip-tab)

There is also a convenience `make` command to generate the .zip file:
```shell
make zip
```


NOTE: This plugin is provided for free and without any warranties
#TODO:
- [ ] readme ;)
- [x] Plugin name: "H3 Toolbox" vs "H3 Toolkit"
- [x] Use H3 logo svg
- [x] H3 Attribution: can refer to H3 as "the H3 discrete global grid system", link to https://h3geo.org, note that H3 library is "© 2022 Uber Technologies, Inc."
- [ ] update metadata.txt
- [x] Handle gracefully if h3 libs not present, guide user on how to install
- [ ] check against QGIS coding style guide, public plugin repository requirements. also see [Releasing your plugin](https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/releasing.html)
- [x] localization to NL, HU? If not, remove `tr()` functions
- [ ] [documentation](https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/plugins.html#documentation)
 



Feedback from H3 community(Nick Rabinowitx):
>At first glance this looks great! We've been interested in a QGIS plugin for a while, but none of the H3 folks were experts in the software (or had the spare time). Your contribution is definitely appreciated!
>- The name “H3 Toolbox” sounds fine to me (maybe I'd go with "toolkit", but :shrug:). AFAIK we don't have any particular concerns about copyright here, and you're free to use the term “H3” as you like.
>- Same goes for the logo, I think it should be fine to use in this context.
>- For attribution, I don't think we have specific text, but you can refer to "the H3 discrete global grid system" or just "the H3 grid system" and link to https://h3geo.org/, and probably note that the H3 library is "© 2022 Uber Technologies, Inc." I don't think any in-code copyright notices are needed.