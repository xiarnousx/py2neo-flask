from py2neo import Graph, Node, Relationship, NodeMatcher
from passlib.hash import bcrypt
from datetime import datetime
import uuid


graph = Graph(host="db", port="7687", auth=("neo4j", "ihab"))


class Tag:
    def __init__(self, tag):
        self.tag = tag

    def find(self):
        matcher = NodeMatcher(graph)
        tag = matcher.match("Tag", name=self.tag)
        return tag.first()

class Post:

    def recent_post(self, n):
        query = """
            MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
            WHERE post.date = {today}
            RETURN user.username as username, post, COLLECT(tag.name) as tags
            ORDER BY post.timestamp DESC
            LIMIT {n}
        """

        today = datetime.now().strftime("%F")

        return list(graph.run(query, today=today, n=n).data())

    def recent_post_by_username(self, username, n):
        query = """
           MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
           WHERE user.username = {username}
           RETURN post, COLLECT(tag.name) as tags
           ORDER BY post.timestamp DESC
           LIMIT {n}
        """

        return list(graph.run(query, username=username, n=n).data())

    def find_by_id(self, id):
        matcher = NodeMatcher(graph)
        post = matcher.match("Post", id=id)
        return post.first()

class User:
    def __init__(self, username):
        self.username = username

    def find(self):
        matcher = NodeMatcher(graph)
        user = matcher.match("User", username=self.username)
        return user.first()

    def register(self, password):
        if not self.find():
            user = Node("User", username=self.username, password=bcrypt.encrypt(password))
            graph.create(user)
            return True

        return False

    def verify_password(self, password):
        user = self.find()

        if not user:
            return False

        return bcrypt.verify(password, user['password'])

    def add_post(self, title, tags, text):
        user = self.find()
        today = datetime.now()

        post = Node(
            "Post",
            id=str(uuid.uuid4()),
            title=title,
            text=text,
            timestamp=int(today.strftime("%s")),
            date=today.strftime("%F")
        )

        rel = Relationship(user, "PUBLISHED", post, on=today.strftime("%F"))
        graph.create(rel)


        tags = [x.strip() for x in tags.lower().split(",")]
        tags = set(tags)

        for t in tags:
            tag = Tag(t)

            tagNode = tag.find()

            if not tagNode:
                tagNode = Node("Tag", name=t)


            tagRel = Relationship(tagNode, "TAGGED", post)

            graph.create(tagRel)

    def like_post(self, post_id):
        user = self.find()
        postObj = Post()
        post = postObj.find_by_id(post_id)
        LIKES = Relationship.type("LIKES")
        graph.merge(LIKES(user, post))

    def similar_users(self, n):
        query="""
            MATCH (a:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(t:Tag),
            (b:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(t)
            WHERE a.username = {username} AND a <> b
            WITH b, COLLECT(DISTINCT t.name) AS tags, COUNT(DISTINCT t.name) as tag_count
            ORDER BY tag_count DESC LIMIT {n}
            RETURN b.username as similar_user, tags
        """

        return list(graph.run(query, username=self.username, n=n).data())

    def commonality_of_user(self, user):
        query="""
        MATCH (a:User)-[:PUBLISHED]->(p:Post)<-[:LIKES]-(b:User)
        WHERE a.username = {username1} AND b.username = {username2}
        RETURN count(p) AS likes
        """

        likes = list(graph.run(query, username1=self.username, username2=user.username).data())

        likes = 0 if not likes[0] else likes[0]['likes']

        query="""
        MATCH (a:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(t:Tag),
        (b:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(t)
        WHERE a.username = {username1} AND b.username = {username2}
        RETURN COLLECT(DISTINCT t.name) AS tags 
        """

        tags = list(graph.run(query, username1=self.username, username2=user.username))[0]['tags']

        return {"likes": likes, "tags": tags}