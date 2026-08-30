from odoo import models, fields, api
import re

class TeacherVideo(models.Model):
    _name = "voca.teacher.video"
    _description = "Teacher Videos"

    
    youtube_url = fields.Char(string="YouTube URL", required=True)
    embed_url = fields.Char(string="Embed URL", compute="_compute_embed_url", store=True)

    teacher_id = fields.Many2one("voca.teacher", string="Teacher", ondelete="cascade")
    masterclass_id = fields.Many2one("master.classes", string="Masterclass", ondelete="cascade")
    
    
    
    @api.depends("youtube_url")
    def _compute_embed_url(self):
        """
        Extracts the video ID from the provided YouTube URL and generates an embeddable URL.
        """
        for record in self:
            video_id = None
            url = record.youtube_url

            if url:
                # Match different YouTube URL formats
                match = re.search(r"(?:youtu\.be/|youtube\.com/(?:embed/|watch\?v=|v/|.+/))([^?&]+)", url)
                if match:
                    video_id = match.group(1)

            # Construct the embed URL if a valid video ID was found
            record.embed_url = f"https://www.youtube.com/embed/{video_id}" if video_id else ""

