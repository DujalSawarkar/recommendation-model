import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class PostRecommender:
    def __init__(self, post_vectors, posts_df, interaction_matrix, user_factors, users_df, views_exploded):
        self.post_vectors = post_vectors
        self.posts_df = posts_df
        self.interaction_matrix = interaction_matrix
        self.user_factors = user_factors
        self.users_df = users_df
        self.views_exploded = views_exploded

    def get_user_content_profile(self, user_id):
        user_views = self.views_exploded[self.views_exploded['userId'] == user_id]
        viewed_post_ids = user_views['tagId'].tolist()
        weights = user_views['weight'].values

        viewed_vectors = self.post_vectors[self.posts_df['_id'].isin(viewed_post_ids)]

        if viewed_vectors.shape[0] == 0:
            return np.zeros((1, self.post_vectors.shape[1]))

        if len(weights) == 0:
            return viewed_vectors.mean(axis=0)

        weighted_vectors = viewed_vectors.multiply(weights[:, None])
        return weighted_vectors.sum(axis=0) / weights.sum()

    def recommend_posts(self, user_id, top_n=5):
        user_profile = self.get_user_content_profile(user_id)
        content_scores = cosine_similarity(user_profile, self.post_vectors).flatten()

        post_ids = self.posts_df['_id'].tolist()
        collab_scores = np.zeros(len(post_ids))

        if user_id in self.interaction_matrix.index:
            user_index = self.interaction_matrix.index.get_loc(user_id)
            user_collab_scores = self.user_factors[user_index]
            collab_score_dict = dict(zip(self.interaction_matrix.columns, user_collab_scores))
            collab_scores = np.array([collab_score_dict.get(post_id, 0) for post_id in post_ids])

        popularity_scores = self.posts_df['popularity_score'].values

        # Normalize scores
        content_scores = content_scores / content_scores.max() if content_scores.max() > 0 else content_scores
        collab_scores = collab_scores / collab_scores.max() if collab_scores.max() > 0 else collab_scores
        popularity_scores = popularity_scores / popularity_scores.max() if popularity_scores.max() > 0 else popularity_scores

        # Get age group weight
        user_age_group = self.users_df.loc[self.users_df['_id'] == user_id, 'age_group'].values[0] if user_id in self.users_df['_id'].values else 'unknown'
        age_weight = {'teen': 1.0, 'young_adult': 1.2, 'adult': 1.1, 'senior': 0.9, 'unknown': 1.0}
        age_group_weight = age_weight.get(user_age_group, 1.0)

        # Combine scores with randomness
        combined_scores = (
            0.4 * content_scores +
            0.3 * collab_scores +
            0.25 * popularity_scores +
            0.03 * age_group_weight +
            np.random.normal(0, 0.02, len(content_scores))
        )

        # Exclude user's own posts
        user_posts = self.posts_df[self.posts_df['userId'] == user_id]['_id'].tolist()
        recommended_indices = [
            i for i in np.argsort(combined_scores)[-top_n * 2:][::-1]
            if post_ids[i] not in user_posts
        ][:top_n]

        return self.posts_df.iloc[recommended_indices][['_id', 'postMessage', 'popularity_score']]

    def recommend_global_posts(self, top_n=5):
        popularity_scores = self.posts_df['popularity_score'].values

        if popularity_scores.max() > 0:
            popularity_scores = popularity_scores / popularity_scores.max()

        combined_scores = (
            0.9 * popularity_scores +
            np.random.normal(0, 0.02, len(popularity_scores))
        )

        recommended_indices = np.argsort(combined_scores)[-top_n:][::-1]
        return self.posts_df.iloc[recommended_indices][['_id', 'postMessage', 'popularity_score']]