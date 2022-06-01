# Python script to export Network Containers from Infoblox

This is a bare bones script that:
1. Pulls network containers in JSON format
2. Changes the keys and values to match Infoblox CSV formats
3. Converts to CSV

The resulting _.csv_ file that is created in the same directory will have the run time stamp in the name.

Make sure to update the following variables to match your Grid:
- **gm_ip**   : Grid manager IP address
- **gm_user** : Username
- **gm_pwd**  : Password
- **net_view**: Network View name

The usual JSON response may not include all necessary fields (expecially if the field value is empty). Is such cases, if required, find and update the __field_list__ variable with the list of necessary fields to include them in the CSV file

Feel free to modify as needed.

Enjoy
