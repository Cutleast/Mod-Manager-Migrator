# Hardlinks vs Copying a file

**Hardlinks can only be used on the same disk and partition. If migrating to another disk and/or partition, hardlinks cannot be used and the files have to copied.**

| Feature            | Hard Link                                  | Copying a File                          |
|--------------------|------------------------------------------|-----------------------------------------|
| **Storage Usage**  | Saves space (points to the same data)    | Uses additional disk space (duplicates data) |
| **Speed**         | Instant creation                         | Takes time proportional to file size    |
| **Data Consistency** | Always reflects changes to the original | Changes affect only the copied version  |
| **File Deletion**  | Data remains until all links are removed | Original and copy are independent       |
| **Cross Filesystem Support** | Only works within the same filesystem | Works across different filesystems      |
| **Backup Behavior** | May not be backed up as a separate file | Each copy is independent for backups    |
| **Risk of Unintended Changes** | High—modifying one modifies all | Low—copy is independent from original   |

Learn more about hardlinks: [https://en.wikipedia.org/wiki/Hard_link](https://en.wikipedia.org/wiki/Hard_link)
