package dog;

/* ======================= 
 * Data managed by a puppy
 * =======================
 *
 * Basic Structures
 * ================
 *
 * - crsobj:
 *   name(string): unique case-insensitive id. Can be the keyword 'all'.
 *
 *   status(string):
 *
 *
 * - user: This is the core data structure a puppy(as well as a dog) will manage they have the following properties:
 * 	id(string): 
 * 		a case-insensitive unique id.
 * 	pwd(string):
 * 		a case-sensitive password.
 * 	
 * 	crscode(object):
 * 		a collection of *crsobj* objects with unique access keys.
 * 	
 * Files
 * =====
 * One data will be in a read/write file uniquely named with
 * an *id*. Only one puppy can be *assigned* a
 * single file at any particular point in time.
 * The file will contain the following
 * structures:
 * 	id(string): same as the filename.
 *
 * 	pwd(string):
 * 		This is set once on file creation. It provides minimal access control and it's case sensitive.
 *
 * 	assigned(boolean):
 * 		Whether or not a puppy is already assigned.
 *
 * 	load(object):
 * 		lcount(int): A unique number incremented for any new load.
 *
 * 		data(object): A collection of *user* objects.
 *
 * Another corresponding data will be in a
 * read-only file uniquely named by reversing
 * preceding filename, e.g from 'id123' to
 * '321di'. This file is created by a dog. It is
 * read by a puppy to display info of a user
 * (like slots, load status etc). It contains to following:
 * 	
 * 	lcount(int): The last lcount processed above.
 *
 * 	trace(object): A collection of *user* objects.
 *
 * 	journal(object): for use by a dog.
 *
 *
 */

public class Puppy
{
    Puppy();


}
