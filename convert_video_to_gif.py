#/usr/bin/env python
from subprocess import call
from moviepy.editor import (
    VideoFileClip,
    CompositeVideoClip,
    TextClip,
    ImageClip,
    concatenate
)

from numpy.testing import assert_approx_equal

from os import listdir
from os.path import expanduser, isfile, getsize

def process_video(filename, video_height=480, overwrite=False):

    gif_name = 'gifs/' + filename + '.gif'

    if isfile(gif_name) and overwrite == False:
        print "Skipping " + gif_name + " as it already exists."
        return 
    
    video_file = VideoFileClip(filename)

    try:
        assert_approx_equal(float(video_file.w)/float(video_file.h),16.0/9.0)
        video_file = video_file.crop(x1=video_file.w/8, x2=7*video_file.w/8)
    except:
        print "Not resizing video."


    video_file = video_file.resize(height=video_height)

    end_image = video_file.to_ImageClip(0).set_duration(0.7)
    
    video_file = concatenate([video_file, end_image])

    logo_size = video_height/6
    text = ImageClip(expanduser("~/dropbox/bslparlour/twitter_logo2.png")).set_duration(video_file.duration).resize(width=logo_size).set_pos((video_file.w-logo_size,video_file.h-logo_size))


    composite_video_file = CompositeVideoClip([video_file, text])
    composite_video_file.write_gif(gif_name,fps=20)

    fuzz_amt = 5
    commands = 'gifsicle "'+gif_name+'" -O3 | convert -fuzz '+str(fuzz_amt)+'% - -ordered-dither o8x8,16 -layers optimize-transparency "'+gif_name+'"'

    process = call(commands, shell=True)

    if getsize(gif_name) > 3*1024**2-50:
        process_video(filename, video_height=video_height*0.75, overwrite=True)

if __name__ == '__main__':
    from multiprocessing import Pool
    p = Pool(processes=4)
    q = Pool(processes=4)
    p.map(process_video, [x for x in listdir('.') if x.find('.mp4') != -1])
    q.map(process_video, [x for x in listdir('.') if x.find('.mov') != -1])
    # for filename in [x for x in listdir('.') if x.find('.mp4') != -1]:
    #     process_video(filename)

    # for filename in [x for x in listdir('.') if x.find('.mov') != -1]:
    #     process_video(filename)
