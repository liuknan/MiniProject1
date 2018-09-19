#!/usr/bin/env python
# encoding: utf-8
import tweepy #https://github.com/tweepy/tweepy
import re
import json
import urllib.request
import os
import io
import subprocess as sp
import google.cloud.vision
from PIL import Image,ImageDraw,ImageFont
same=[]
img_list=[]
imgnum_list=[]
from google.cloud import videointelligence
#Twitter API credentials

API_key = "enter your keys"
API_secret_key = "enter your keys"
access_token = "enter your keys"
access_token_secret = "enter your keys"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='upload your json file'

def get_images(screen_name):
    ##authorization
    auth = tweepy.OAuthHandler(API_key, API_secret_key)
    auth.set_access_token(access_token, access_token_secret)
    api=tweepy.API(auth)
    alltweets=[]
    new_tweets = api.user_timeline(screen_name=screen_name, count=30)
    alltweets.extend(new_tweets)
    oldest = alltweets[-1].id - 1
    while len(new_tweets) > 0:

        # all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name=screen_name, count=30, max_id=oldest,tweet_mode='extended')

        # save most recent tweets
        alltweets.extend(new_tweets)

        # update the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1
        if (len(alltweets) > 30):
            break
        print
        "...%s tweets downloaded so far" % (len(alltweets))

    # write tweet objects to JSON
    file = open('tweet.json', 'w')
    print
    "Writing tweet objects to JSON please wait..."
    for status in alltweets:
        json.dump(status._json, file, sort_keys=True, indent=4)

    # close the file
    print
    "Done"
    file.close()

def get_image_url(file):
        ##read json, since that file is not an valid file.
        text=open(file,'r')
        for line in text.readlines():
            ##find urls
            urltext = re.compile(r'media_url": "(.*)",')
            url=urltext.findall(line)
            ##remove the same url
            if len(url):
                if url[0] in same:
                    continue
                else:
                    same.insert(-1,url[0])

            else:
                continue
            ##line = line.replace("'", "")
            ##images = json.loads(line)
            ##for m in images['entities'] ['media'].values():
                ##print("%s" % (m['display_url']))
def download_images(list):
    file = open('url.txt','w')
    ##read file and download urls
    num = 1
    for n in list:
        nam = str(num)
        nam=nam.zfill(4)
        file.write(n+'\n')
        n=str(n)
        ##name='./'+str(random.randrange(0,1000))+'.jpg'
        name=n.replace("http://","")
        name=name.replace("/","_")
        img_list.insert(-1,name)
        ##dir=os.path.abspath('.')+'/images'
        ##if not os.path.exists(dir):
            ##os.mkdir(dir)
        ##else:

       ## file_path=os.path.join(dir,n)
        ##rename the pictures so that the ffmpeg could convert them to a video.
        urllib.request.urlretrieve(n,'img'+nam+'.jpg')
        imgnum=str(num)
        ##number the file
        imgnum_list.insert(-1,'img'+imgnum.zfill(4)+'.jpg')
        num = num + 1
    file.close()

def video_output():
    # input_file = 'video.mp4'
    # out_file = 'video_out.mp4'
    # img_data= list
    # video.ins_img(input_file, img_data,out_file)
    ##use command line to start the ffmpeg.
    ctrcmd='ffmpeg -r 1/2 -i img%004d.jpg  -y test.mp4'
    sp.call(ctrcmd,shell=True)

def image_detection():
    # Create a Vision client.
    vision_client = google.cloud.vision.ImageAnnotatorClient()

    # TODO (Developer): Replace this with the name of the local image
    # file to analyze.
    i=0
    for name in imgnum_list:

        image_file_name = imgnum_list[i]
        with io.open(image_file_name, 'rb') as image_file:
            content = image_file.read()

    # Use Vision to label the image based on content.
        image = google.cloud.vision.types.Image(content=content)
        response = vision_client.label_detection(image=image)
        im = Image.open(name)
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype('/Library/Fonts/Trattatello.ttf',32)
        x,y=(0,0)
        print('Labels:')
        for label in response.label_annotations:
            draw.text((x,y),label.description,fill='red',font=font)
            y=y+40
            im.save(imgnum_list[i])
            print(label.description)
        i=i+1

def video_detction(path): ##https://cloud.google.com/video-intelligence/docs/libraries
    """Detect labels given a file path."""
    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.enums.Feature.LABEL_DETECTION]

    with io.open(path, 'rb') as movie:
        input_content = movie.read()

    operation = video_client.annotate_video(
        features=features, input_content=input_content)
    print('\nProcessing video for label annotations:')

    result = operation.result(timeout=90)
    print('\nFinished processing.')

    # Process video/segment level label annotations
    segment_labels = result.annotation_results[0].segment_label_annotations
    for i, segment_label in enumerate(segment_labels):
        print('Video label description: {}'.format(
            segment_label.entity.description))
        for category_entity in segment_label.category_entities:
            print('\tLabel category description: {}'.format(
                category_entity.description))

        for i, segment in enumerate(segment_label.segments):
            start_time = (segment.segment.start_time_offset.seconds +
                          segment.segment.start_time_offset.nanos / 1e9)
            end_time = (segment.segment.end_time_offset.seconds +
                        segment.segment.end_time_offset.nanos / 1e9)
            positions = '{}s to {}s'.format(start_time, end_time)
            confidence = segment.confidence
            print('\tSegment {}: {}'.format(i, positions))
            print('\tConfidence: {}'.format(confidence))
        print('\n')

    # Process shot level label annotations
    shot_labels = result.annotation_results[0].shot_label_annotations
    for i, shot_label in enumerate(shot_labels):
        print('Shot label description: {}'.format(
            shot_label.entity.description))
        for category_entity in shot_label.category_entities:
            print('\tLabel category description: {}'.format(
                category_entity.description))

        for i, shot in enumerate(shot_label.segments):
            start_time = (shot.segment.start_time_offset.seconds +
                          shot.segment.start_time_offset.nanos / 1e9)
            end_time = (shot.segment.end_time_offset.seconds +
                        shot.segment.end_time_offset.nanos / 1e9)
            positions = '{}s to {}s'.format(start_time, end_time)
            confidence = shot.confidence
            print('\tSegment {}: {}'.format(i, positions))
            print('\tConfidence: {}'.format(confidence))
        print('\n')

    # Process frame level label annotations
    frame_labels = result.annotation_results[0].frame_label_annotations
    for i, frame_label in enumerate(frame_labels):
        print('Frame label description: {}'.format(
            frame_label.entity.description))
        for category_entity in frame_label.category_entities:
            print('\tLabel category description: {}'.format(
                category_entity.description))

        # Each frame_label_annotation has many frames,
        # here we print information only about the first frame.
        frame = frame_label.frames[0]
        time_offset = frame.time_offset.seconds + frame.time_offset.nanos / 1e9
        print('\tFirst frame time offset: {}s'.format(time_offset))
        print('\tFirst frame confidence: {}'.format(frame.confidence))
        print('\n')
if __name__ == '__main__':
    get_images('@FoAMortgage')
    get_image_url('tweet.json')
    download_images(same)
    image_detection()
    video_output()
    video_detction('/Users/liuknan/PycharmProjects/APIAssignment/test.mp4')

##for status in tweepy.Cursor(api.home_timeline).items(2):
##    print (status.txt)

##alltweets = []

