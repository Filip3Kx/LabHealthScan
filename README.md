# Overview
This is an application that takes data from test setups working in the lab and scans their SSH and RDP ports to represent what might not be working.

I don't think anyone would make this work on their PC's without going into the code because it's made to display a very specific set of data.

## Key features
- Displays data grouped by racks
- Every list item acts as a link to the server web application running on port 8732 when double clicked.
- The top list items are power switches in a certain rack. They will open a raritan web interface when double clicked.
- Scans port 22 (SSH) for the DUT's
- Scans port 3389 (RDP) for the CTRL's
- List refreshes every minute 


## Excel format
Sample Servers excel file @plik.tmp

| Name | Dut | Ctrlr | Rack |
| --- | --- | --- | --- |

Sample Raritan excel file 

| Rack | IP |
| --- | --- | 
