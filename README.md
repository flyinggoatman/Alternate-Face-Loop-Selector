# Alternate Face Loop Selector for Blender

Quickly select alternating face loops (horizontal or vertical) within Blender's Mesh Edit Mode, streamlining your workflow by automating repetitive selections.

---

## Overview

This Blender addon simplifies selecting alternating face loops by intelligently analysing your mesh's topology. Save time and improve your workflow efficiency when working with complex mesh selections.

---

## Features

* **Easy Alternating Selections:** Quickly select every other face loop.
* **Configurable Settings:** Customise skip count and iteration depth.
* **Debug Mode:** Optional detailed output for troubleshooting.

---

## Installation

1. Download the addon files.
2. Open Blender and go to  **Edit → Preferences → Add-ons** .
3. Click  **Install** , select the downloaded `.py` file, and enable the addon.

---

## Usage

* Enter **Edit Mode** on a mesh object and ensure **Face Select** mode is active.
* Select an initial face (or faces) to define your starting loop.
* Open the **Sidebar** (`N`) and navigate to the **Select** panel.
* Click  **"Select Alternate Face Loops"** .
* Adjust the settings in the operator panel to refine your selection.
* Alternatively, you can use the **Control+F** menu in Edit Mode to quickly access the operator.

---

## Parameters

* **Skip Count:** Number of loops to skip between selected loops.
* **Repeat:** Maximum iterations for the selection process.
* **Debug Mode:** Toggle detailed output for debugging purposes.

---

## Compatibility

Tested with Blender 4.4.x. Compatible with most quad-based meshes.

---

## License

Distributed under the [GPL-3.0-or-later](https://spdx.org/licenses/GPL-3.0-or-later.html) License.

---

## Contributing

Suggestions and improvements are welcome. Please open an issue or submit a pull request.

---

*Happy Blending!*
