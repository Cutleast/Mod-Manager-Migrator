# Hardlinks

## Definition

A hard link is a directory entry that associates a name with a file. Thus, each file must have at least one hard link. Creating additional hard links for a file makes the contents of that file accessible via additional paths (i.e., via different names or in different directories). This causes an alias effect: a process can open the file by any one of its paths and change its content.

Learn more about hardlinks: [https://en.wikipedia.org/wiki/Hard_link](https://en.wikipedia.org/wiki/Hard_link)

**Note: Hardlinks can only be used on the same disk and partition. If migrating to another disk and/or partition, hardlinks cannot be used and the files have to copied.**

## Hardlinks vs Copying a file

| Feature                              | Hard Link                                | Copying a File                               |
| ------------------------------------ | ---------------------------------------- | -------------------------------------------- |
| **Storage Usage**                    | Saves space (points to the same data)    | Uses additional disk space (duplicates data) |
| **Speed**                            | Instant creation                         | Takes time proportional to file size         |
| **Data Consistency**                 | Always reflects changes to the original  | Changes affect only the copied version       |
| **File Deletion**                    | Data remains until all links are removed | Original and copy are independent            |
| **Cross Filesystem Support**         | Only works within the same filesystem    | Works across different filesystems           |
| **Risk of Unintended Changes**       | High — modifying one modifies all        | Low — copy is independent from original      |
