---
layout: post
title: "memo: a bug which double close the socket acceptor fd"
date: 2020-09-07 08:07:31 +0900
categories: Programming
tags: Network 
---

A exception raises with the rate around 10% in all execution in Mac OS:

```console
libc++abi.dylib: terminating with uncaught exception of type boost::wrapexcept<boost::system::system_error>: cancel: Bad file descriptor
Process 14336 stopped
```
Found that the acceptor fd is closed twice:

```cpp
   181 	    void event(int, const message::ConnectionEvent& e) override {
   182 	        switch (e) {
   183 	            case message::ConnectionEvent::timeout:
-> 184 	                stop();
   185 	                break;
   186 	            case message::ConnectionEvent::close:
   187 	                break;
```

The stop will call the server to stop and close the opening fd of accept(). This stop will be called whenever a timeout event occurs.

By the logs, seems that the asio timer `cancel` is correctly been called, but it is not canceled immediatly:

```console
  [0] = "2020-09-07 07:44:03.920797 DEBUG tid:0x7000085d4000 in server.cpp:35 Accepting connection from 127.0.0.1"
  [1] = "2020-09-07 07:44:03.920797 DEBUG tid:0x700008657000 in client.cpp:27 Successfully connect to 127.0.0.1"
  [2] = "2020-09-07 07:44:03.928531 DEBUG tid:0x700008657000 in connection.cpp:314 Send heartbeat to 127.0.0.1:50265."
  [3] = "2020-09-07 07:44:03.928914 DEBUG tid:0x7000085d4000 in connection.cpp:249 Receive heartbeat from 127.0.0.1:50266"
  [4] = "2020-09-07 07:44:03.934058 DEBUG tid:0x700008657000 in connection.cpp:314 Send heartbeat to 127.0.0.1:50265."
  [5] = "2020-09-07 07:44:03.935789 WARN tid:0x7000085d4000 in connection.cpp:268 Peer socket: 127.0.0.1:50266 timeout"
  [6] = "2020-09-07 07:44:03.935929 DEBUG tid:0x7000085d4000 in heartbeat.cpp:42 The heartbeat timer is cancelled."
  [7] = "2020-09-07 07:44:03.936252 DEBUG tid:0x7000085d4000 in connection.cpp:249 Receive heartbeat from 127.0.0.1:50266"
  [8] = "2020-09-07 07:44:03.936356 DEBUG tid:0x7000085d4000 in server.cpp:39 Acceptor stopped"
  [9] = "2020-09-07 07:44:03.937584 ERROR tid:0x700008657000 in connection.cpp:291 Server: 127.0.0.1:50265 closes connection."
  [10] = "2020-09-07 07:44:03.937829 DEBUG tid:0x700008657000 in connection.cpp:307 Timer of socket id 127.0.0.1:50265: Operation canceled"
  [11] = "2020-09-07 07:44:03.942797 WARN tid:0x7000085d4000 in connection.cpp:268 Peer socket: 127.0.0.1:50266 timeout"
  [12] = "2020-09-07 07:44:03.942868 DEBUG tid:0x7000085d4000 in heartbeat.cpp:42 The heartbeat timer is cancelled."
```

The  connection will be closed immediatly when timer expires:

```cpp
void ServerConnectionWithHeartbeat::when_timeout(const std::error_code &ec) {
    if (ec) {
        if (ec.value() == asio::error::operation_aborted)
            // could be the timer reset or stop the heartbeat
            return;
        else {
            TI_ERROR(format("Error when {} timer expires: {}",
                            socket_to_string(), ec.message()));
        }
    } else {
        TI_WARN(format("Peer socket: {} timeout", socket_to_string()));
        connection_close();
        upper_layer_event_callback(message::ConnectionEvent::timeout);
    }
}
```

 But seems the connection is not "closed" immediately: Log 6 shows that the server received the heartbeat very soon after the timer is canceled, and invoke a callback to restart the timer. Then we see the timer timeout again, trigger a timeout event and the server stops again.

No time to examine whether there could still be a reading event in kqueue after close is called in MacOS, but just keep that case down here.
