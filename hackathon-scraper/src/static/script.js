document.addEventListener('DOMContentLoaded', function() {
    const hackathonContainer = document.getElementById('hackathon-container');

    fetch('data/hackathons.json')
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                hackathonContainer.innerHTML = '<p>No hackathons found.</p>';
                return;
            }

            data.forEach(hackathon => {
                const hackathonElement = document.createElement('div');
                hackathonElement.classList.add('hackathon');

                const title = document.createElement('h3');
                title.textContent = hackathon.title;

                const date = document.createElement('p');
                date.textContent = `Date: ${hackathon.date}`;

                const link = document.createElement('a');
                link.href = hackathon.link;
                link.textContent = 'View Hackathon';
                link.target = '_blank';

                hackathonElement.appendChild(title);
                hackathonElement.appendChild(date);
                hackathonElement.appendChild(link);
                hackathonContainer.appendChild(hackathonElement);
            });
        })
        .catch(error => {
            console.error('Error fetching hackathon data:', error);
            hackathonContainer.innerHTML = '<p>Error loading hackathons.</p>';
        });
});