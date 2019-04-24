    
# YouTube Data Collection

There are two s for collecting data on YouTube: `youtube_channel_loader.py` and `youtube_related_channels.py`. We talk about them separately.

## `youtube_channel_loader.py`

- **Usage** (saving errors and output to a log file):
 

    python ./youtube_tools/youtube_channel_loader.py src_csv dst_folder > log.txt 2>&1
    
- `src_csv`: This scripts receives a `.csv` file with channels, some  categories/sub-categories and the channel Id.

        Name,Category,Sub-Category,Data Collection step,Id
        Howard Dare,Manosphere,MGTOW,1,Ucs-brcHDxKqrOGU9cEWuCMQ
        Ronin Man,Manosphere,MGTOW,1,Ucj5j4pIgg8gtcRA4iYTWiAg
        Sandman,Manosphere,MGTOW,1,UCeCV-XNeZIoHiCGfNYCLh9Q

- `dst_folder`: Specify an existing folder where the script will save several `.csv` files with the `captions`, `channel_id`, `comments`,`description`, `dislike_count`, `like_count`, `name`, `title`, `upload_date`,`video_id` and `view_count` for each of the videos in that channel (up to 2,500). Each file will be called `{video_id}.csv`.


 To obtain a channel Id sometimes you need to desambiguate a username. [You can do this online](https://commentpicker.com/youtube-channel-id.php).