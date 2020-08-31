---
layout: post
title: "Class Interface design and thread-safe in concurrent programming"
date: 2020-08-31 22:00:03 +0900
categories: Programming
tags: concurent, thread-safe
---


# Class Interface design and thread-safe in concurrent programming

I wrote a logging manager for logging. The logging manager maintains a thread-safe queue and creates a new thread for asynchronous logging, let's call it logging thread. The queue is used to deliver logging records to the logging thread which is doing an infinite loop of retrieving records from that queue until a stop token received.
 
 The interface of the logging manager is below:
 ```cpp
 class GlobalLoggerManager {
  private:
	threadsafe_queue queue;
    std::thread logging_deamon;
  public:
    GlobalLoggerManager(int level);
    GlobalLoggerManager(int level, const char *file_path);
    void new_records(const record &r);
    void loop_body();
    void stop();
};
 ```

Every public method seems to be OK now: `new_records()` will place a new record into the queue,  and `loop_body()` is the logic for the logging thread. By calling the `stop()`, we can stop the thread.

the implementation of loop body:
```cpp
while(not stopped){
    string msg;
    record_queue.receive(msg); // block until there is something to receive
    if is not stop tokent {  // empty str is a marker to stop
        _dest << msg;   // log goes to the destination
	}
}
```
This loop is running in the daemon thread.

One cool thing of such an implement is the logging operation, which could be expensive with IO, is done asynchronously. But the problem is, whenever I get the return from the `new_records()`, there is no guarantee that the log is actually written to the destination, it might still be in the queue, waiting to be fetched by the logging daemon. Sometimes this is undesirable. For example, I'd like to verify the logging result immediately in unit tests. So I try to add the following methods:
 ```cpp
 class GlobalLoggerManager {
  private:
	threadsafe_queue queue;
    std::thread logging_deamon;
  public:
    GlobalLoggerManager(int level);
    GlobalLoggerManager(int level, const char *file_path);
    void new_records(const record &r);
    void flush_all(); // new method
    void loop_body();
    void stop();
};
 ```

the `flush_all` method allows us to flush all records in the queue to the daemon thread (not necessary to disk). This interface looks good, right? Sadly, no, it makes no sense. I discovered that only after I wrote error implementation.

The problem is:

 1. There is no way to force the logging thread to "accelerate". We have
    to wait.
  2. The sematic of flush_all is ill-formed.

You might think "flush_all" is to block until all records go to the logging thread. This is OK if all `new_records()` is called only in the same thread where the `flush_all()` is called. We can guarantee that there are no more `new_records` at the point when we call `flush_all()`. But in the multi-thread environment, what is the definition of **all records**. No, there could be another thread to do the `new_records()` in the future. You might think, "OK, so that let's interpret the flush_all as flush all records in the queue at the point of invoking flush_all". But, that' still makes no sense. The infinite loop will **eventually** received these logs in the memory. There is no difference for the whole system between
	- the main thread stops and waits for a certain  (unpredictable) set of records received by the logging thread.
	- the main thread does no flush_all.

As a result, `flush_all` makes no sense in a multithreaded environment. It is quite common that the designing of the interface directly affects the feasibility of implementing a thread-safe class. That is one thing I learned in this case: when designing the interface, thing twice for the thread-safe.

Another example of thread-safe interface is `pop()` and `top()` method in std::stack. The pop here returns void and delete the top object in the stack. To achieve the traditional "pop and return" semantics, you need to call top() to get the object first and then pop(). The reason for such a design is exception free. If we merge these 2 operations, have a T pop(), an exception could be thrown during the pop() since pop is to delete the old and create a new one. However, creating the new object is not exception free.

This design is problematic in concurrent programming. The stack class with separeate `pop` and `top` will no longer be thread safe, even if all methods of std::stack themselves are thread-safe. Let's look at the example:
```cpp
if(s.size() > 0){
	t = s.top();
	s.pop();
}
```
At the instant between 3 methods calls, anything could happen. Maybe there is another thread just empty the whole stack. Then, the program is corrupted. We need to apply a lock on the region even if all methods are thread-safe.

Back to the problem at the beginning. If we want a way to ensure the records has been received by the logging thread, we need to add logic to the thread who creates logs to define at which point (which log) we want to wait for, and write new codes to the logging thread to allow the logging thread tell us all everything is done.
