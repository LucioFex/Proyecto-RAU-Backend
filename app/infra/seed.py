from app.schemas.users import UserCreate
from app.schemas.communities import CommunityCreate
from app.schemas.posts import PostCreate
from app.schemas.comments import CommentCreate
from app.repositories.memory.users_repo import UsersRepo
from app.repositories.memory.communities_repo import CommunitiesRepo
from app.repositories.memory.posts_repo import PostsRepo
from app.repositories.memory.comments_repo import CommentsRepo

def seed_minimal(users: UsersRepo, comms: CommunitiesRepo, posts: PostsRepo, comments: CommentsRepo):
    # Usuarios demo (si no existen)
    prof = users.get_by_email("prof@ucema.edu.ar")
    if not prof:
        prof_pub = users.create(UserCreate(
            name="Profe Demo", email="prof@ucema.edu.ar", username="prof",
            role="Profesor", password="secret123"
        ))
        prof = users.get_by_email("prof@ucema.edu.ar")
    est = users.get_by_email("est@ucema.edu.ar")
    if not est:
        est_pub = users.create(UserCreate(
            name="Estudiante Demo", email="est@ucema.edu.ar", username="estu",
            role="Estudiante", password="secret123"
        ))
        est = users.get_by_email("est@ucema.edu.ar")

    prof_id = prof["id"]
    est_id = est["id"]

    # Comunidades demo (si no hay)
    if not comms.data:
        c1 = comms.create(CommunityCreate(name="Ingeniería Informática", description="Carrera UCEMA"))
        c2 = comms.create(CommunityCreate(name="Algoritmos y Estructuras", description="AAyED"))
        c3 = comms.create(CommunityCreate(name="Redes II", description="Routing, TCP/IP, BGP"))

        # Membresías básicas
        comms.join(c1.id, prof_id)
        comms.join(c1.id, est_id)
        comms.join(c2.id, est_id)
        comms.join(c3.id, est_id)

        # Posts demo
        p1 = posts.create(prof_id, PostCreate(
            community_id=c1.id, title="Bienvenidos a RAU", content="Reglas básicas y recursos", tag="Anuncio"
        ))
        p2 = posts.create(est_id, PostCreate(
            community_id=c2.id, title="Duda sobre complejidad", content="¿O(log n) vs O(n)? ejemplo práctico", tag="Pregunta"
        ))
        p3 = posts.create(est_id, PostCreate(
            community_id=c3.id, title="Apuntes para el parcial", content="Comparto mi resumen en PDF", tag="Recurso"
        ))

        # Comentarios demo
        comments.create(p1.id, est_id, CommentCreate(content="¡Gracias, profe!"))
        comments.create(p2.id, prof_id, CommentCreate(content="Traé el caso y lo vemos."))
        comments.create(p3.id, prof_id, CommentCreate(content="Buen material."))
