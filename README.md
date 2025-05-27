![Project Logo](./__icon__.ico)  
# Push Board

## Overview  
**Push Board** is a PyQt5-based GUI tool designed to efficiently push device configurations to multiple network devices in parallel. It is tailored for large-scale network migrations, upgrades, and provisioning projects, simplifying management and execution of configuration pushes.

## Features  
- Add, edit, and manage configuration snippets with real-time editing support.  
- Embed native checkboxes for configuration options, ensuring clean UI and accurate status tracking.  
- Push configurations concurrently to one or more devices with live status updates.  
- Import configuration sets from CSV files for bulk operations.  
- Persist configuration sessions and user settings reliably via JSON-backed persistent storage.  
- Context menu for quick access to add, push, abort, import, clear, and delete operations.  
- Smart one-line configuration preview, truncating long configs for better readability without cutting words abruptly.  

## Migration Lifecycle  
- Pre-Migration  
- Post-Migration  
- Live Deployment  

## Usage  
- Add devices and their configuration snippets via the "Add" button or import CSV files.  
- Use native checkboxes in the table to select which configurations to save or push.  
- Push all or selected configurations using context menu actions or toolbar buttons.  
- Abort ongoing pushes at any time with easy interface controls.  
- Configuration and checkbox state changes are instantly persisted to disk, ensuring data integrity between sessions.  
- Track push status updates live directly in the table view.

## Tags  
`#ConfigPush` `#Netmig` `#Automation` `#NetworkMigration` `#DeviceProvisioning` `#Cisco` `#Infrastructure` `#MassDeployment` `#PushTool` `#PyQt5`
