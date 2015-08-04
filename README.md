# LucidGTK
GTK application for running Google's DeepDream software on Linux systems

Much of the code is taken from Google's deepdream iPython notebook (https://github.com/google/deepdream) and repackaged in to a GTK application with the intention of making it simpler to experiment with the various settings (models, output layers, iterations, octaves. etc.)

## Install:

* NB. You will need to have Caffe (http://caffe.berkeleyvision.org/) installed in order to use Lucid

    Download the latest release tarball from http://rebelweb.co.uk/lucid-gtk/<br />
    Unpack the tar.gz<br />
    Open a terminal and navigate to the unpacked folder<br />
    Enter the following commands and enter your password if prompted:<br />
        
        ./configure
        make
        sudo make install

        lucid-gtk
        
    Now you can use the lucid-gtk command in a terminal anytime you wish to start the application
