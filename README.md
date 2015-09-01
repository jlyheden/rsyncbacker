# initial idea

time machine in osx is not flexible enough and slow, thus this "script" aims to:

* run rsync backups unattended (ie cron) on laptops (only care about osx for now)
* allow post hooks (such as triggering snapshot in freenas)
* optional to only trigger when being on same lan as backup target

# revised idea

while initial idea was kiss it would be nice to encrypt the data on the target and not have the keys
to the castle stored under entrance door mat to the castle, thus the revised idea
takes another step closer to what time machine does, creating a sparsebundle on
afp share that is double mounted onto the client machine, and then rsyncing between source and the mounted
destination image. historical archive is still implemented using snapshots on the target (freenas)

# running it

clone this repo, cd into it and run

```
virtualenv venv
source venv/bin/activate
python setup.py install
```

create an afp file share on your nas and record the details in your config yml (see example.yml)

to execute the backup:

```
rsyncbacker_cmd.py path/to/your/config.yml
```

this will

* mount the afp share (if not mounted)
* check if image exists on share and create if not
* mount the image (if not mounted)
* run backup
* execute post hook (if any configured)
* umount image
* umount afp share

# todo

* tests are 100% inaccurate and broken
