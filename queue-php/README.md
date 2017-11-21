very basic setup to play with rabbitmq with php.
(taken from https://www.rabbitmq.com/tutorials/tutorial-one-php.html.)

setup
-----

php and composer is required to setup.

to install rabbitmq:

    brew install rabbitmq

to install the php rabbitmq library:

    composer install

it will just install the required library from ``composer.json`` file from this repository.

running
-------

once you have set up you can try running rabbitmq and the php scripts:

1. run the rabbitmq server.
2. run the sender script, this will define the "hello" queue", and put "Hello World!" into the queue.
3. run the receiver script, this will monitor the "hello" queue, print out all the items, waits for new items and then print them all out too.

you would open 3 terminal tabs/windows for each step above.

to run the rabbitmq server:

    rabbitmq-server

to run the sender script: (in a separate tab)

    php sender.php

do this as many times as you like. each time ``sender.php`` will push a new item to the "hello" queue.

to run the receiver script: (in a separate tab)

    php receiver.php

this should immediaitely print out all the items from the "hello" queue if you had ran ``sender.php``.
it will continue to wait for new items, so go back to the sender tab and run ``sender.php`` a few more times,
you should see more items being printed out in the receiver tab as you run the sender script.

when you are finished, you want to stop the receiver script and the rabbitmq-server.
to do so, go into those tabs and press ``CTRL-C``.
