# Map balance statistics for Rising Storm 2: Vietnam

## Enable balance logging

In order to begin logging map balance statistics in server logs,
navigate to your server's `Config\ROEngine.ini` file and in `[Core.System]`
section, remove the following line `Suppress=DevBalanceStats`.

After a server restart, balance stat will begin to be logged in `Log\Launch.log`. 

## Analyzing logs

For best results, logs from a long time period will be gathered and then analyzed.
Ideally, the log file(s) would be manually collected before or after each server restart
to a persistent location, because the server will clean up old log files periodically.

### Example scenario:

Server logs from a server have been collected into `E:\collected_logs`.
The contents of the folder are the following:
```
E:\collected_logs\Launch-backup-2020.03.29-00.21.00.log
E:\collected_logs\Launch-backup-2020.03.29-00.23.36.log
E:\collected_logs\Launch-backup-2020.04.05-19.13.57.log
E:\collected_logs\Launch-backup-2020.04.05-19.52.52.log
E:\collected_logs\Launch-backup-2020.04.06-14.00.18.log
E:\collected_logs\Launch-backup-2020.04.07-03.34.45.log
E:\collected_logs\Launch-backup-2020.04.08-15.08.14.log
E:\collected_logs\Launch.log
```

To analyze the logs, `ParseStats.exe` is executed with the following arguments:
`ParseStats.exe "E:\ww_logs\*" "E:\collected_logs\results\stats.csv"
--player-threshold 16 --analyze`

The first argument is the path to log file(s) to analyze.
The `*` character is a wildcard, denoting all the files in `E:\ww_logs\`.
The second argument is the stats output file. The third argument, `--player-threshold X`, filters
off the matches where the number of players was fewer than X when the match ended. The fourth
argument, `--analyze` tells the program to analyze results. Analysis results are written in the
same folder as the `stats.csv` file was in the example.

## Dowload

From releases: https://github.com/tuokri/rs2stats/releases
