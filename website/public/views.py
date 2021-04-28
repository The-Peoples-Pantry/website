from datetime import date
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "public/index.html"

    @property
    def extra_context(self):
        return {
            'volunteers_lower_bound': 500,
            'meal_requests_lower_bound': 15_000,
            'grocery_requests_lower_bound': 11_000,
        }


class MediaView(TemplateView):
    template_name = "public/media.html"
    extra_context = {
        "stories": sorted([
            {
                'title': 'Food Justice, Sovereignty, & Security',
                'author': "The People's Pantry",
                'date': date.fromisoformat('2021-03-05'),
                'link': 'https://www.youtube.com/watch?v=DR6SMDL4jYo',
                'image': 'media/food-justice-panel.png',
                'outlet': 'YouTube'
            },
            {
                'title': "The People's Pantry in Toronto provides free home-cooked meals to those in need",
                'author': 'Olivia Little',
                'date': date.fromisoformat('2021-01-11'),
                'link': 'https://www.blogto.com/eat_drink/2021/01/peoples-pantry-toronto-provides-free-home-cooked-meals-those-need/',
                'image': 'media/blogto.png',
                'outlet': 'BlogTO'
            },
            {
                'title': 'The Peoples Pantry is Helping Combat Food Insecurity',
                'author': 'Stella Acquisto',
                'date': date.fromisoformat('2020-07-28'),
                'link': 'https://toronto.citynews.ca/video/2020/07/28/peoples-pantry-helping-combat-food-insecurity/#:~:text=combat%20food%20insecurity',
                'image': 'media/citynews-1.jpg',
                'outlet': 'CityNews Toronto'
            },
            {
                'title': 'Food is Love: Volunteers look to continue feeding Toronto with The People’s Pantry',
                'author': 'Lyndsay Morrison',
                'date': date.fromisoformat('2020-10-14'),
                'link': 'https://toronto.ctvnews.ca/food-is-love-volunteers-look-to-continue-feeding-toronto-with-the-people-s-pantry-1.5145374',
                'image': 'media/citynews-2.jpg',
                'outlet': 'CityNews Toronto'
            },
            {
                'title': 'The Exception as the Rule: Toronto’s social reproduction organizing in the age of COVID-19',
                'author': 'Lina Nasr, El Hag Ali, and Olena Lyubchienko',
                'date': date.fromisoformat('2020-10-14'),
                'link': 'https://spectrejournal.com/the-exception-as-the-rule/',
                'image': 'media/spectre.jpg',
                'outlet': 'Spectre'
            },
            {
                'title': 'People’s Pantry and creating inclusive spaces for migrants during the pandemic (PDF).',
                'author': 'Dominik Formanowicz',
                'date': date.fromisoformat('2020-11-03'),
                'link': 'https://www.ryerson.ca/content/dam/centre-for-immigration-and-settlement/RCIS/publications/spotlightonmigration/2020_3_Formanowicz_Dominik_People\'s_Pantry_and_creating_inclusive_spaces_for_migrants_during_the_pandemic.pdf',
                'image': 'media/ryerson.jpg',
                'outlet': 'Ryerson’s spotlight on migration'
            },
            {
                'title': 'Sociology students build grassroots volunteer-run initiative to help those in need during COVID-19 pandemic.',
                'author': 'Sherri Klassen',
                'date': date.fromisoformat('2020-04-24'),
                'link': 'https://sociology.utoronto.ca/sociology-students-build-grassroots-volunteer-run-initiative-to-help-those-in-need-during-covid-19-pandemic/',
                'image': 'media/utoronto.jpg',
                'outlet': 'University of Toronto'
            },
            {
                'title': 'The People’s Pantry Gives Free Food to Torontonians Experiencing Food Insecurity.',
                'author': 'Al Donato',
                'date': date.fromisoformat('2020-06-03'),
                'link': 'http://www.huffingtonpost.ca/entry/peoples-pantry-free-food-toronto_ca_5ed163a2c5b64d62dd502851',
                'image': 'media/huffpo.jpg',
                'outlet': 'HuffPo Canada'
            },
            {
                'title': 'Grad student addresses food insecurity in Ontario as co-founder of a grassroots community initiative.',
                'author': 'Stephanie Shaw',
                'date': date.fromisoformat('2020-08-13'),
                'link': 'https://yfile.news.yorku.ca/2020/08/13/laps-student-addresses-food-insecurity-in-ontario-with-grassroots-community-initiative-note-use-they-their-pronouns/',
                'image': 'media/yfile.jpg',
                'outlet': 'York University yFile'
            },
            {
                'title': 'Reasons to Love Toronto. No. 1: Because our home chefs are feeding the hungry',
                'author': 'Caroline Aksich',
                'date': date.fromisoformat('2020-10-20'),
                'link': 'https://torontolife.com/city/reasons-to-love-toronto/no-1-because-our-home-chefs-are-feeding-the-hungry/',
                'image': 'media/torontolife.jpg',
                'outlet': 'Toronto Life'
            },
            {
                'title': 'Covid-19: Food Justice and Mutual Aid in the Pandemic (Webinar)',
                'author': '',
                'date': date.fromisoformat('2020-05-19'),
                'link': 'https://www.facebook.com/110190900641866/videos/2779922052293971',
                'image': 'media/mutualaid.jpg',
                'outlet': 'Toronto/Tkaronto Mutual Aid'
            },
            {
                'title': 'Organizing During a Pandemic: Lessons for the Left (Webinar)',
                'author': '',
                'date': date.fromisoformat('2020-06-23'),
                'link': 'https://www.youtube.com/watch?v=s2uw5GWrTKI',
                'image': 'media/sis.jpg',
                'outlet': 'SIS Salon'
            },
        ], key=lambda story: story['date'], reverse=True)
    }


class AboutView(TemplateView):
    template_name = "public/about.html"

    @property
    def extra_context(self):
        return {
            'testimonials': [
                'testimonials/crystal.png',
                'testimonials/jan.png',
                'testimonials/liz.png',
                'testimonials/wanyi.png',
            ]
        }


class RecipesView(TemplateView):
    template_name = "public/recipes.html"
