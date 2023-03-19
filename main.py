import argparse
import glob
import os
import threading
import random
import subprocess
import time
import signal
from Xlib import X, display, Xutil, Xatom, error

parser = argparse.ArgumentParser()
parser.add_argument("dir")
args = parser.parse_args()

class DemoPlayer:
    def __init__(self, dir, num_tiles=3):

        self.video_width = 1280
        self.video_height = 1100

        self.dir = dir
        self.rescan()

        self.exit_requested = False

        self.threads = []
        signal.signal(signal.SIGINT, self.stop)
        for i in range(num_tiles):
            new_thread = threading.Thread(target=self.thread, args=(i,))
            new_thread.start() 
            self.threads.append(
                new_thread
            )

    def run(self):
        while not self.exit_requested:
            time.sleep(0.5)

    def stop(self, sig, frame):
        self.exit_requested = True
        for thread in self.threads:
            thread.join()
        print("All threads completed, exiting.")

    def resize_window(self, window_title, x, y, w, h):
        get_xprop = lambda disp, win, prop: win.get_full_property(disp.intern_atom('_NET_WM_' + prop), 0)

        disp = display.Display()
        root = disp.screen().root
        tree = root.query_tree()
        wins = tree.children

        for win in wins:
            for subwin in win.query_tree().children:                    
                window_name_prop = get_xprop(disp, subwin, 'NAME')
                if window_name_prop:
                    window_name = window_name_prop.value.decode("utf-8")
                    if window_name == window_title:
                        win_geometry = win.get_geometry()
                        if win_geometry.x != x or win_geometry.y != y or win_geometry.width != w or win_geometry.height != h:
                            print("Moving VLC window to x=%d, y=%d, w=%d, h=%d from %d, %d, %d, %d" % (x, y, w, h, win_geometry.x, win_geometry.y, win_geometry.width, win_geometry.height))
                            subwin.change_property(disp.intern_atom("_MOTIF_WM_HINTS"), disp.intern_atom("_MOTIF_WM_HINTS"), 32, [0x2, 0x0, 0x0, 0x0, 0x0])
                            subwin.configure(x=x, y=y, width=w, height=h, border_width=0, stack_mode=X.Above)
                            disp.sync()
                            disp.flush()
                        return True
        return False      

    def thread(self, tile_x=0):
        last_video_id = None
        while True:
            while True:
                video_id = random.randrange(0, len(self.all_demos) - 1)
                if video_id != last_video_id:
                    break
            last_video_id = video_id
            print("Thread %d now playing: %s" % (tile_x, self.all_demos[video_id]))
            video_window_title = "VLC window %d" % (tile_x)
            cmd_line = [
                "vlc", 
                "-Idummy", 
                "--gles2=any",
                "--no-video-deco", 
                "--no-embedded-video",
                "--video-title",
                video_window_title,
                "--width=%d" % (self.video_width),
                "--height=%d" % (self.video_height), 
                "--no-autoscale",
                self.all_demos[video_id]
            ]
            video_proc = subprocess.Popen(cmd_line)
            while True:
                try:
                    self.resize_window(video_window_title, tile_x * self.video_width, 0, self.video_width, self.video_height)
                except error.BadWindow:
                    pass
                if self.exit_requested:
                    print("Exit requested, killing VLC in thread %d " % (tile_x))
                    video_proc.kill()
                    return
                try:
                    video_proc.wait(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    pass

    def play(self, video, tile_x=0):
        window_x = self.video_width * tile_x

    def rescan(self):
        self.all_demos = []
        for f in glob.glob(os.path.join(self.dir, "**.mp4"), recursive=True):
            self.all_demos.append(f)

if __name__ == "__main__":
    demoplayer = DemoPlayer(args.dir)
    demoplayer.run()