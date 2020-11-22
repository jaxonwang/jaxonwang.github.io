---
layout: post
title: "Notes on the google spanner paper"
date: 2020-11-22 21:54:24 +0900
categories: Programming
tags: distrbuted, database
---

# The traits of Google Spanner 
1. horizontal scalability, keys partitioned into shards(named "Directory" in the paper)
2.  Transaction and extern consistency
3.  RW transactions require 2 phase commit and 2 phase locking with locks stored on a lock table on each Span Master
4. R only transactions requires no lock and no 2 phase commit. Read is fast since the client query it's the nearest replica and reads the latest data, likely without blocking (Even no Paxos sync latency).

# The organization of Spanner
1.  Each span server controls a set of directories, one Paxos group.
2. One strong leader for each Paxos group, providing good performance 
3. Seems that the lock-table and transaction manager are on the replica leader.
4. When the client desire a transaction, choose the nearest leader as the coordinator leader to perform 2 phase commit

# What is the client
1. Client performs transaction through the APIs to Spanner
2. In a transaction, the client queries all needed data (acquires read locks), process and then ask the coordinator to commit them (read locks now upgraded to write locks).
3. In a transaction, the client keeps sending heartbeats to keepalive the ownership of locks.

![](https://user-images.githubusercontent.com/10634580/99905786-60b5f500-2d16-11eb-83c1-f60814ae8b91.png)

# A globally distributed clock is the key to achieve linearizability

If there is a global clock which returns a precise time, all events in the system can be ordered easily, preserving the "happens-before" relation in real-time:

> Lamport, L. (2019). Time, clocks, and the ordering of events in a distributed system. In _Concurrency: the Works of Leslie Lamport_ (pp. 179-196).

But in a distributed system, what we can do best is maintaining the global clock as a time range. A slight adjustment would help us achieve linearizability. Spanner uses Marzullo's algorithm, in which the range size will converge with the rounds of synchronization:

> Marzullo, K., & Owicki, S. (1983, August). Maintaining the time in a distributed system. In _Proceedings of the second annual ACM symposium on Principles of distributed computing_ (pp. 295-305).

Every read/ R only transaction is associated with a timestamp. The timestamp is used for ordering, does not necessarily related to the time of events. Spanner might assign an earlier timestamp, preserving the linearizability, to an R only transaction for better performance (4.14).

Every RW transaction is associated with a timestamp $s$, which is after the client submission time but before the commit time. (#0)

All reads in an R/RW transaction are associated with the same timestamp, which must be larger than any finished RW transactions (#1)

For all transactions, if transaction A happens before transaction B (B starts after A commits), then A's timestamp is strictly smaller than B's. (#2)

Serving Reads at a Timestamp(4.1.3): A read to key $X$ with timestamp $s_1$ will get the latest value of $X$ in all RW transactions with timestamps smaller than $s_1$ (#3)

By #1 and #2 and #3 and #0, we have the linearizability. By 2 phase locking and 2 phase commit, we have the serializability. 

For better performance, read timestamps should be as early as possible, commit timestamps should be as late as possible.

## To satisfy #0
After receving commit request from client, the coordinator assigns a RW transaction $T_i$ a commit timestamp $s_i >=t_{abs}(e_{i}^{server})$.  By the Commit Wait rule, the coordinator will wait unitl $s_i$ passes. Then #2 is satisfied (proved in 4.1.2)

## To satisfy #3
Only serve read with timestamp $t<=t_{safe}$. If $t$ is safe, serve the latest copy of data (If I am correct here, only the latest version of data is stored, no need to store older versions. That's different from what Professor stated in MIT 6.824 class). We need to make sure the data to serve is newer than the client could see when it requests, and not to be the intermediate data inside other transactions (4.1.3: $t_{safe}^{TM} = \min(s_i^{prepare}) - 1$).

## To satisfy #1
The timestamp for reads must be larger than any finished RW transaction. 
- For a single span server read transaction, Spanner tracks the latest RW transaction's timestamp in this Spanserver and sets the timestamp as early as possible.
- For multi-site read transactions, just set the timestamp to now().latest. That avoids the negotiation. Correctness lies in the fact that now().latest is strictly newer than all finished RW transactions' timestamp.

## Optimization
if $t_{safe}^{Paxos}$ doesn't advance, a read could be blocked indefinitely (4.2.4). That's a similar problem I face when implementing KVRaft. It can be solved if there is a periodic Paxos logging with an empty command, indicating there is no log entry on the fly. But it is easier if we have a strong leader and leader's leases disjoint. Just ask the leader since the leader must know the latest Paxos write. Further optimization can advance the $t_{safe}^{Paxos}$ to the minimum value the leader could assign in the next Paxos write.

## In Paxos
Only the leader can assign a timestamp, and the leader only chooses timestamps within its lease. The leases between the leaders are disjoint.  
