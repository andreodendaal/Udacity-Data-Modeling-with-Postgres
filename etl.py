import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    # open song file
    df = pd.read_json(filepath, lines=True)
        
    df_selected = df[['song_id', 'title', 'artist_id', 'year', 'duration']]
    song_data_array = df_selected.values[0]

    # insert song record
    song_data = song_data_array.tolist()
    cur.execute(song_table_insert, song_data)    
    
    # insert artist record
    df_artist = df[['artist_id', 'artist_name', 'artist_location', 'artist_latitude', 'artist_longitude']] 
    artist_data_array = df_artist.values[0]

    artist_data = artist_data_array.tolist()
    cur.execute(artist_table_insert, artist_data)
    
    return    
    

def process_log_file(cur, filepath):
    
    # open log file
    df = pd.read_json(filepath, lines=True)

    # filter by NextSong action
    df = df[(df.page == "NextSong")]

    # convert timestamp column to datetime
    df["ts"] = pd.to_datetime(df["ts"])     
       
    # Extract and insert time data records
    time_data = [df.ts, df.ts.dt.time, df.ts.dt.hour, df.ts.dt.day, df.ts.dt.week, df.ts.dt.month, df.ts.dt.year, df.ts.dt.weekday]
    column_labels = ['timestamp','time','hour', 'day', 'week of year', 'month', 'year', 'weekday']
    time_dict = dict(zip(column_labels, time_data))
    
    time_df = time_df = pd.DataFrame(time_dict)

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = df[['userId', 'firstName', 'lastName' , 'gender', 'level']].drop_duplicates()

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
  
    for i_key, row in df.iterrows():        
        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None        
 
        # insert songplay record
        songplay_data = (i_key, row.ts, row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent)
        cur.execute(songplay_table_insert, songplay_data)
        
    return
        

def process_data(cur, conn, filepath, func):
    # get all files matching extension from directory
    
    print(filepath, func)
    
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))
        
    print('{}/{} files processed.'.format(i, num_files)) 
    
    return


def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()