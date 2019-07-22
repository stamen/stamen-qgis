# Stamen QGIS plugin

This QGIS plugin provides an assortment of processing algorithms and other tools used for GIS and data visualization purposes.

The pacakge is maintained by Stamen Design, a San Francisco-based data visualization studio. We use these tools internally to create beautiful and informative maps, and we invite feature requests and contributions.

## Plugin features

_Processors_

- Create hulls from points (improved concave/convex hulls)

## Installation

_This plugin requires QGIS >= 3.0._

To install the latest published version within QGIS, go to _Plugins_ -> _Manage and Install Plugins..._ and search for Stamen.

## Development

To install locally for development, clone this repository to your QGIS plugins directory. Alternatively, you can clone to a different path and create a link to it within your QGIS plugins directory, if your filesystem supports linking. Here are some default QGIS 3.x plugin directory paths for various platforms:

- macOS: `~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins`
- Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
- Windows: `C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`

We recommend using the [Plugin Reloader](https://github.com/borysiasty/plugin_reloader) plugin during development. Use Plugin Reloader to reload the Stamen plugin with QGIS open and see your changes. (Note that changes to metadata.txt require restarting QGIS.)

We use [pb_tool](https://g-sherman.github.io/plugin_build_tool) to build and deploy. You may need to modify the `plugin_path` in pb_tool.cfg to deploy.

### Building

`pb_tool compile` (compiles resource files, etc.)

### Deploying locally

`pb_tool deploy`

This command will deploy to your local plugins directory. It's not necessary if you've cloned this repo to your plugins directory, but it can be used to simulate a user installation.

### Deploying to QGIS

`pyclean . && pb_tool zip`

The above commands will clean the project directories of build artifacts and generate a ZIP archive for the plugin. Sign into the [QGIS plugins web portal](http://plugins.qgis.org/) with your [OSGeo Services UserID](https://www.osgeo.org/community/getting-started-osgeo/osgeo_userid/) and upload the generated archive.
