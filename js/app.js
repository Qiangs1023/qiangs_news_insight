
// Vue应用
const { createApp } = Vue;

createApp({
    data() {
        return {
            articles: [],
            filteredArticles: [],
            searchQuery: '',
            selectedSource: '',
            selectedDate: ''
        }
    },
    mounted() {
        this.loadArticles();
    },
    methods: {
        async loadArticles() {
            try {
                const response = await fetch('data/articles.json');
                const data = await response.json();
                this.articles = data.articles;
                this.filteredArticles = this.articles;
                this.populateSourceFilter();
            } catch (error) {
                console.error('Error loading articles:', error);
            }
        },
        populateSourceFilter() {
            const sources = [...new Set(this.articles.map(a => a.source_name))];
            const select = document.getElementById('sourceFilter');
            sources.forEach(source => {
                const option = document.createElement('option');
                option.value = source;
                option.textContent = source;
                select.appendChild(option);
            });
        },
        filterArticles() {
            let filtered = this.articles;

            // 搜索过滤
            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase();
                filtered = filtered.filter(a =>
                    (a.title && a.title.toLowerCase().includes(query)) ||
                    (a.content && a.content.toLowerCase().includes(query))
                );
            }

            // 源过滤
            if (this.selectedSource) {
                filtered = filtered.filter(a => a.source_name === this.selectedSource);
            }

            // 日期过滤
            if (this.selectedDate) {
                const now = new Date();
                const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

                filtered = filtered.filter(a => {
                    const articleDate = new Date(a.published_at);
                    if (this.selectedDate === 'today') {
                        return articleDate >= today;
                    } else if (this.selectedDate === 'week') {
                        const weekAgo = new Date(today);
                        weekAgo.setDate(weekAgo.getDate() - 7);
                        return articleDate >= weekAgo;
                    } else if (this.selectedDate === 'month') {
                        const monthAgo = new Date(today);
                        monthAgo.setMonth(monthAgo.getMonth() - 1);
                        return articleDate >= monthAgo;
                    }
                    return true;
                });
            }

            this.filteredArticles = filtered;
        }
    }
}).mount('#app');
