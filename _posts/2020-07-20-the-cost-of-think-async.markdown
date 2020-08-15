---
layout: post 
title:  "the cost of think-async"
date:   2020-07-20 16:50:47 +0900
categories: Programming 
tags: asio c++
---

We need to guarantee that the callback functions and everything bound to them should be available when the asio executor running them. I just forgot that...


```cpp
void server(execution_context &ctx){
   std::error_code ec;
   ti_socket_t skt = {0, resolve("127.0.0.1", ec)};
   AsyncServer s{ctx, skt};
 }

 int main()
 {
   logging_init(0);
   server(ctx);
   ctx.run();
 }
```

That's a silly mistake, isn't it?
Well, I just spend a huge time locating this silly bug.
Since the compiled program doesn't produce a segment fault. Luckily, I enabled the undefined behavior sanitizer.

```console
/usr/include/c++/7/bits/invoke.h:73:46: runtime error: member call on address 0x7fffffffda90 which does not point to an object of type 'AsyncServer'
0x7fffffffda90: note: object has a possibly invalid vptr: abs(offset to top) too big
 ff 7f 00 00  80 01 00 00 10 61 00 00  d0 d8 ff ff ff 7f 00 00  d0 da ff ff ff 7f 00 00  40 01 00 00
              ^~~~~~~~~~~~~~~~~~~~~~~
              possibly invalid vptr
```

Backtrace doesn't help too much since it is called asynchronously. What I can see from the stack is just complicated asio async call stack ....
That's the cost to write async...
