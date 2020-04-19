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
`ParseStats.exe "E:\collected_logs\*" "E:\collected_logs\results\stats.csv"
--player-threshold 16 --analyze`

The first argument is the path to log file(s) to analyze.
The `*` character is a wildcard, denoting all the files in `E:\collected_logs\`.
The second argument is the stats output file. The third argument, `--player-threshold X`, filters
off the matches where the number of players was fewer than X when the match ended. The fourth
argument, `--analyze` tells the program to analyze results. Analysis results are written in the
same folder as the `stats.csv` file was in the example.

After executing the command the following output is produced:
```
writing output to 'E:\collected_logs\results\stats.csv'
analyzing statistics...
total entries: 123
matches played:
        WWTE-Mannerheim: 27
        WWTE-Boreal: 18
        WWTE-Kollaa: 12
        WWTE-KuhmoOutskirts: 10
        WWTE-Salla: 10
        WWTE-Tolvajarvi: 9
        WWTE-MutarantaKurgan: 7
        WWSU-Tolvajarvi: 7
        WWTE-Suomussalmi: 6
        WWTE-Raatteentie: 6
        WWTE-Aittojoki: 5
        WWTE-Summa: 4
        WWTE-MutarantaKurgain: 2

win ratios:
        WWSU-Tolvajarvi: num_axis_win=5, num_allies_win=2, allies_win_rate=28.6%
        WWTE-Aittojoki: num_axis_win=2, num_allies_win=3, allies_win_rate=60.0%
        WWTE-Boreal: num_axis_win=15, num_allies_win=3, allies_win_rate=16.7%
        WWTE-Kollaa: num_axis_win=9, num_allies_win=3, allies_win_rate=25.0%
        WWTE-KuhmoOutskirts: num_axis_win=7, num_allies_win=3, allies_win_rate=30.0%
        WWTE-Mannerheim: num_axis_win=21, num_allies_win=6, allies_win_rate=22.2%
        WWTE-MutarantaKurgain: num_axis_win=1, num_allies_win=1, allies_win_rate=50.0%
        WWTE-MutarantaKurgan: num_axis_win=4, num_allies_win=3, allies_win_rate=42.9%
        WWTE-Raatteentie: num_axis_win=4, num_allies_win=2, allies_win_rate=33.3%
        WWTE-Salla: num_axis_win=2, num_allies_win=8, allies_win_rate=80.0%
        WWTE-Summa: num_axis_win=3, num_allies_win=1, allies_win_rate=25.0%
        WWTE-Suomussalmi: num_axis_win=4, num_allies_win=2, allies_win_rate=33.3%
        WWTE-Tolvajarvi: num_axis_win=5, num_allies_win=4, allies_win_rate=44.4%

win conditions:
        WWSU-Tolvajarvi: ROWC_ScoreLimit=7
        WWTE-Aittojoki: ROWC_AllObjectiveCaptured=2,ROWC_TimeLimit=2,ROWC_LockDown=1
        WWTE-Boreal: ROWC_TimeLimit=12,ROWC_AllObjectiveCaptured=3,ROWC_LockDown=3
        WWTE-Kollaa: ROWC_LockDown=5,ROWC_TimeLimit=4,ROWC_ReinforcementsDepleted=3
        WWTE-KuhmoOutskirts: ROWC_AllObjectiveCaptured=7,ROWC_ReinforcementsDepleted=3
        WWTE-Mannerheim: ROWC_TimeLimit=13,ROWC_LockDown=7,ROWC_AllObjectiveCaptured=6,ROWC_OverTime=1
        WWTE-MutarantaKurgain: ROWC_AllObjectiveCaptured=1,ROWC_TimeLimit=1
        WWTE-MutarantaKurgan: ROWC_TimeLimit=4,ROWC_AllObjectiveCaptured=3
        WWTE-Raatteentie: ROWC_ReinforcementsDepleted=4,ROWC_AllObjectiveCaptured=2
        WWTE-Salla: ROWC_AllObjectiveCaptured=7,ROWC_TimeLimit=2,ROWC_ReinforcementsDepleted=1
        WWTE-Summa: ROWC_LockDown=3,ROWC_AllObjectiveCaptured=1
        WWTE-Suomussalmi: ROWC_AllObjectiveCaptured=4,ROWC_LockDown=2
        WWTE-Tolvajarvi: ROWC_AllObjectiveCaptured=5,ROWC_LockDown=2,ROWC_ReinforcementsDepleted=1,ROWC_TimeLimit=1

writing summary to file 'E:\collected_logs\results\stats_summary.txt'
```

The summary file (`stats_summary.txt`) will contain more information that is too
verbose to be show in the console window.

## Download

From releases: https://github.com/tuokri/rs2stats/releases
