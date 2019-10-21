import os
import glob
import logging

from feedgen.feed import FeedGenerator

music_dir = '/home/eric/rpodcast_code/rpodcast-snippets-python/ogg_source/'  # Path where the videos are located
my_files = glob.glob("/home/eric/rpodcast_code/rpodcast-snippets-python/ogg_source/*.mp3")
print(my_files)

my_files.sort(key=os.path.getmtime)

for file in my_files:
    print(file)



fg = FeedGenerator()


# general feed params
fg.id('https://r-podcast.org')
fg.title('R-Snippets')
fg.author( {'name':'Eric Nantz', 'email':'thercast@gmail.com'})
fg.link(href='https://r-podcast.org', rel='alternate' )
fg.logo('https://imgur.com/Mr70QS9')
fg.subtitle('Musings on R, open-source, and life')
fg.link( href='https://r-podcast.org/rsnippets.xml', rel='self')
fg.language('en')

fg.load_extension('podcast')

# podcast-specific params
fg.podcast.itunes_category('Technology')
fg.podcast.itunes_author('Eric Nantz')
fg.podcast.itunes_explicit('no')
fg.podcast.itunes_owner('Eric Nantz', 'thercast@gmail.com')
fg.podcast.itunes_summary('Musings on R, open-source, and life')

# add feed entries
# ------------------- notes ------------------
# fe = fg.add_entry()
# fe.title('R-Snippet X')
# fe.link('https://r-podcast.org')
# fe.author( {'name':'Eric Nantz', 'email':'thercast@gmail.com'} )
# fe.enclosure(url='https://rpodcast-snippets-audio.s3.amazonaws.com/2019-10-13_04-08_377218764.mp3', type = 'audio/mpeg') 
# fe.itunes_summary("Another snippet!")
# fe.itunes_subtitle("Short snippet!")


#for (audio_file in my_files):
#    if audio_file.endswith(".mp3")



#fg.rss_str(pretty=True)
#fg.rss_file('rsnippets.xml')

